// nft_eval: headless quality harness for ARToolKit5 NFT (KPM detection + AR2 tracking).
//
// Renders synthetic camera frames of a planar NFT marker with a KNOWN pose (ground truth), feeds them
// to kpmMatching() / ar2Tracking() and reports detection rate, pose accuracy and timing.
// All randomness comes from a self-contained PRNG so results are reproducible across compilers/OSes.
//
//   nft_eval dataset=<path without ext> image=<marker.jpg> dpi=<dpi used for genTexData> [options]
//   options: mode=detect|track|all  trials=10  seqlen=90  width=640  height=480  fovy=45  seed=1
//            scenarios=scale,tilt,roll,blur,noise,light,occlusion  kpm_proc=1  threads=1  csv=out.csv

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <string>
#include <vector>

#include <AR/ar.h>
#include <AR/param.h>
#include <AR2/imageFormat.h>
#include <AR2/tracking.h>
#include <AR2/util.h>
#include <KPM/kpm.h>

// ------------------------------------------------------------------------------------------------
// Utilities
// ------------------------------------------------------------------------------------------------
namespace {

const double kPi = 3.14159265358979323846;
inline double deg2rad(double d) { return d * kPi / 180.0; }

// xorshift64*: identical sequence on every platform.
struct Rng {
    uint64_t s;
    explicit Rng(uint64_t seed) : s(seed * 0x9E3779B97F4A7C15ull + 0x1234567ull) { for (int i = 0; i < 4; i++) next(); }
    uint64_t next() { s ^= s >> 12; s ^= s << 25; s ^= s >> 27; return s * 0x2545F4914F6CDD1Dull; }
    double u01() { return (double)(next() >> 11) / 9007199254740992.0; }
    double uni(double a, double b) { return a + (b - a) * u01(); }
    double gauss() { double u1 = std::max(u01(), 1e-12), u2 = u01(); return std::sqrt(-2.0 * std::log(u1)) * std::cos(2.0 * kPi * u2); }
};

typedef double Mat3[3][3];
struct Pose { double R[3][3]; double t[3]; };  // marker -> camera (ARToolKit convention, millimetres)

void matMul(const Mat3 a, const Mat3 b, Mat3 out) {
    Mat3 r;
    for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) { r[i][j] = 0; for (int k = 0; k < 3; k++) r[i][j] += a[i][k] * b[k][j]; }
    memcpy(out, r, sizeof(r));
}
void rotAxis(double ax, double ay, double az, double ang, Mat3 R) {
    double n = std::sqrt(ax * ax + ay * ay + az * az); ax /= n; ay /= n; az /= n;
    double c = std::cos(ang), s = std::sin(ang), C = 1 - c;
    R[0][0] = c + ax * ax * C;      R[0][1] = ax * ay * C - az * s; R[0][2] = ax * az * C + ay * s;
    R[1][0] = ay * ax * C + az * s; R[1][1] = c + ay * ay * C;      R[1][2] = ay * az * C - ax * s;
    R[2][0] = az * ax * C - ay * s; R[2][1] = az * ay * C + ax * s; R[2][2] = c + az * az * C;
}

struct Camera { int w, h; double fx, fy, cx, cy; };

// ------------------------------------------------------------------------------------------------
// Marker image source + synthetic frame renderer
// ------------------------------------------------------------------------------------------------
struct Level { int w, h; std::vector<float> px; };

struct Marker {
    std::vector<Level> pyr;  // pyr[0] = full resolution luma
    double dpi = 150.0;
    double widthMM() const { return pyr[0].w / dpi * 25.4; }
    double heightMM() const { return pyr[0].h / dpi * 25.4; }
};

bool loadMarker(const char *jpg, double dpi, Marker &m) {
    char base[1024], ext[64];
    ar2UtilDivideExt(jpg, base, ext);
    AR2JpegImageT *img = ar2ReadJpegImage(base, ext);
    if (!img) { fprintf(stderr, "Cannot read %s\n", jpg); return false; }
    Level l0; l0.w = img->xsize; l0.h = img->ysize; l0.px.resize((size_t)l0.w * l0.h);
    for (int i = 0; i < l0.w * l0.h; i++) {
        if (img->nc == 1) l0.px[i] = img->image[i];
        else { const ARUint8 *p = img->image + i * img->nc; l0.px[i] = 0.299f * p[0] + 0.587f * p[1] + 0.114f * p[2]; }
    }
    ar2FreeJpegImage(&img);
    m.dpi = dpi;
    m.pyr.push_back(std::move(l0));
    while (m.pyr.back().w >= 32 && m.pyr.back().h >= 32) {
        const Level &p = m.pyr.back();
        Level n; n.w = p.w / 2; n.h = p.h / 2; n.px.resize((size_t)n.w * n.h);
        for (int y = 0; y < n.h; y++) for (int x = 0; x < n.w; x++)
            n.px[(size_t)y * n.w + x] = 0.25f * (p.px[(size_t)(2 * y) * p.w + 2 * x] + p.px[(size_t)(2 * y) * p.w + 2 * x + 1] +
                                                 p.px[(size_t)(2 * y + 1) * p.w + 2 * x] + p.px[(size_t)(2 * y + 1) * p.w + 2 * x + 1]);
        m.pyr.push_back(std::move(n));
    }
    return true;
}

inline float sampleBilinear(const Level &L, double x, double y) {  // x,y in pixel-centre coords of the level
    x = std::min(std::max(x, 0.0), L.w - 1.001); y = std::min(std::max(y, 0.0), L.h - 1.001);
    int x0 = (int)x, y0 = (int)y; float fx = (float)(x - x0), fy = (float)(y - y0);
    const float *p = &L.px[(size_t)y0 * L.w + x0];
    return (p[0] * (1 - fx) + p[1] * fx) * (1 - fy) + (p[L.w] * (1 - fx) + p[L.w + 1] * fx) * fy;
}

// Frame pixel -> marker plane millimetres. Returns false if the ray points away from the plane.
bool pixelToPlane(const Pose &P, const Camera &c, double x, double y, double &X, double &Y) {
    double d[3] = {(x - c.cx) / c.fx, (y - c.cy) / c.fy, 1.0};
    double C[3], D[3];
    for (int i = 0; i < 3; i++) {
        C[i] = -(P.R[0][i] * P.t[0] + P.R[1][i] * P.t[1] + P.R[2][i] * P.t[2]);   // camera centre in marker frame
        D[i] = P.R[0][i] * d[0] + P.R[1][i] * d[1] + P.R[2][i] * d[2];             // ray direction in marker frame
    }
    if (std::fabs(D[2]) < 1e-9) return false;
    double s = -C[2] / D[2];
    if (s <= 0) return false;
    X = C[0] + s * D[0]; Y = C[1] + s * D[1];
    return true;
}

void projectMarkerPoint(const Pose &P, const Camera &c, double X, double Y, double &x, double &y) {
    double pc[3];
    for (int i = 0; i < 3; i++) pc[i] = P.R[i][0] * X + P.R[i][1] * Y + P.t[i];
    x = c.fx * pc[0] / pc[2] + c.cx; y = c.fy * pc[1] / pc[2] + c.cy;
}

void gaussianBlur(std::vector<float> &img, int w, int h, double sigma) {
    if (sigma < 0.05) return;
    int r = std::max(1, (int)std::ceil(3 * sigma));
    std::vector<float> k(2 * r + 1); float sum = 0;
    for (int i = -r; i <= r; i++) { k[i + r] = (float)std::exp(-0.5 * i * i / (sigma * sigma)); sum += k[i + r]; }
    for (float &v : k) v /= sum;
    std::vector<float> tmp(img.size());
    for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
        float a = 0; for (int i = -r; i <= r; i++) a += k[i + r] * img[(size_t)y * w + std::min(std::max(x + i, 0), w - 1)];
        tmp[(size_t)y * w + x] = a; }
    for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
        float a = 0; for (int i = -r; i <= r; i++) a += k[i + r] * tmp[(size_t)std::min(std::max(y + i, 0), h - 1) * w + x];
        img[(size_t)y * w + x] = a; }
}

struct Degrade {
    double blurSigma = 0;     // optical blur, px
    double noiseSigma = 0;    // additive gaussian, grey levels
    double gain = 1.0;        // contrast about mid-grey
    double offset = 0;        // brightness
    double ramp = 0;          // horizontal illumination gradient, +-fraction
    double occlusion = 0;     // fraction of the marker's projected bbox covered by a flat patch
    double bgContrast = 1.0;  // background texture amplitude multiplier
};

// Smooth random background so that the marker is not floating on a flat field.
std::vector<float> makeBackground(const Camera &c, Rng &rng, double amp) {
    std::vector<float> bg((size_t)c.w * c.h);
    for (float &v : bg) v = (float)rng.gauss();
    gaussianBlur(bg, c.w, c.h, 6.0);
    float mx = 1e-6f; for (float v : bg) mx = std::max(mx, std::fabs(v));
    for (float &v : bg) v = 115.0f + (float)(amp * 45.0) * v / mx;
    return bg;
}

// Renders one grey-level frame. 'poses' > 1 gives motion blur by averaging sub-frame renders.
void renderFrame(const Marker &m, const Camera &cam, const std::vector<Pose> &poses, const std::vector<float> &bg,
                 const Degrade &dg, Rng &rng, std::vector<uint8_t> &out) {
    std::vector<float> acc((size_t)cam.w * cam.h, 0.0f);
    for (const Pose &P : poses) {
        // Choose a mip level from the source-pixels-per-frame-pixel scale at the marker centre.
        double X0, Y0, X1, Y1, X2, Y2;
        bool ok = pixelToPlane(P, cam, cam.cx, cam.cy, X0, Y0) && pixelToPlane(P, cam, cam.cx + 1, cam.cy, X1, Y1) &&
                  pixelToPlane(P, cam, cam.cx, cam.cy + 1, X2, Y2);
        double scale = 1.0;
        if (ok) {
            double s1 = std::hypot(X1 - X0, Y1 - Y0), s2 = std::hypot(X2 - X0, Y2 - Y0);
            scale = std::max(s1, s2) / 25.4 * m.dpi;
        }
        int lvl = std::min((int)m.pyr.size() - 1, std::max(0, (int)std::floor(std::log2(std::max(scale, 1.0)) + 0.25)));
        const Level &L = m.pyr[lvl]; double ls = (double)(1 << lvl);
        static const double so[2] = {-0.25, 0.25};
        for (int y = 0; y < cam.h; y++) for (int x = 0; x < cam.w; x++) {
            float a = 0;
            for (int sy = 0; sy < 2; sy++) for (int sx = 0; sx < 2; sx++) {
                double X, Y; float v = bg[(size_t)y * cam.w + x];
                if (pixelToPlane(P, cam, x + so[sx], y + so[sy], X, Y)) {
                    double u = X / 25.4 * m.dpi - 0.5, vv = m.pyr[0].h - 0.5 - Y / 25.4 * m.dpi;
                    if (u >= 0 && u <= m.pyr[0].w - 1 && vv >= 0 && vv <= m.pyr[0].h - 1)
                        v = sampleBilinear(L, (u + 0.5) / ls - 0.5, (vv + 0.5) / ls - 0.5);
                }
                a += v;
            }
            acc[(size_t)y * cam.w + x] += a * 0.25f;
        }
    }
    for (float &v : acc) v /= (float)poses.size();

    // Occlusion patch over the marker (use the middle pose).
    if (dg.occlusion > 0) {
        const Pose &P = poses[poses.size() / 2];
        double xs[4], ys[4], W = m.widthMM(), H = m.heightMM();
        projectMarkerPoint(P, cam, 0, 0, xs[0], ys[0]); projectMarkerPoint(P, cam, W, 0, xs[1], ys[1]);
        projectMarkerPoint(P, cam, W, H, xs[2], ys[2]); projectMarkerPoint(P, cam, 0, H, xs[3], ys[3]);
        double x0 = *std::min_element(xs, xs + 4), x1 = *std::max_element(xs, xs + 4);
        double y0 = *std::min_element(ys, ys + 4), y1 = *std::max_element(ys, ys + 4);
        double bw = x1 - x0, bh = y1 - y0, a = std::sqrt(dg.occlusion);
        double pw = bw * std::min(1.0, a * rng.uni(0.8, 1.25)), ph = bh * std::min(1.0, dg.occlusion * bw * bh / std::max(pw * bh, 1.0));
        double px0 = x0 + rng.u01() * (bw - pw), py0 = y0 + rng.u01() * (bh - ph);
        for (int y = std::max(0, (int)py0); y < std::min(cam.h, (int)(py0 + ph)); y++)
            for (int x = std::max(0, (int)px0); x < std::min(cam.w, (int)(px0 + pw)); x++) acc[(size_t)y * cam.w + x] = 70.0f;
    }

    gaussianBlur(acc, cam.w, cam.h, dg.blurSigma);
    out.resize(acc.size());
    for (int y = 0; y < cam.h; y++) for (int x = 0; x < cam.w; x++) {
        double v = acc[(size_t)y * cam.w + x];
        v = (v - 128.0) * dg.gain + 128.0 + dg.offset;
        if (dg.ramp != 0) v *= 1.0 + dg.ramp * ((double)x / cam.w - 0.5) * 2.0;
        if (dg.noiseSigma > 0) v += dg.noiseSigma * rng.gauss();
        out[(size_t)y * cam.w + x] = (uint8_t)std::min(255.0, std::max(0.0, v + 0.5));
    }
}

// ------------------------------------------------------------------------------------------------
// Ground-truth pose generation and error metrics
// ------------------------------------------------------------------------------------------------
struct PoseSpec {
    double distFactor = 1.5;   // multiples of the "marker fills 80% of frame height" distance
    double tiltDeg = 0;        // out-of-plane tilt
    double tiltAzimuthDeg = 0; // direction of tilt axis in the marker plane
    double rollDeg = 0;        // in-plane rotation
    double dxFrac = 0, dyFrac = 0;  // marker-centre offset from frame centre, fraction of frame size
};

Pose makePose(const PoseSpec &s, const Marker &m, const Camera &cam) {
    double W = m.widthMM(), H = m.heightMM();
    double d0 = cam.fy * H / (0.8 * cam.h);
    double Zc = d0 * s.distFactor;
    Mat3 Rbase = {{1, 0, 0}, {0, -1, 0}, {0, 0, -1}};   // marker +Z (out of page) towards the camera, camera y down
    Mat3 Rroll, Rtilt, Rm, R;
    rotAxis(0, 0, 1, deg2rad(s.rollDeg), Rroll);
    rotAxis(std::cos(deg2rad(s.tiltAzimuthDeg)), std::sin(deg2rad(s.tiltAzimuthDeg)), 0, deg2rad(s.tiltDeg), Rtilt);
    // Tilt about the marker's own centre, roll in-plane first.
    matMul(Rtilt, Rroll, Rm);
    matMul(Rbase, Rm, R);
    Pose P; memcpy(P.R, R, sizeof(R));
    double px = cam.cx + s.dxFrac * cam.w, py = cam.cy + s.dyFrac * cam.h;
    double C0[3] = {Zc * (px - cam.cx) / cam.fx, Zc * (py - cam.cy) / cam.fy, Zc};
    // Rotation is about the marker centre (W/2, H/2, 0): t = C0 - R * centre.
    for (int i = 0; i < 3; i++) P.t[i] = C0[i] - (R[i][0] * W * 0.5 + R[i][1] * H * 0.5);
    return P;
}

struct PoseError { double cornerPx, transMM, transRel, rotDeg; };

PoseError comparePose(const Pose &gt, const float est[3][4], const Marker &m, const Camera &cam) {
    Pose E; for (int i = 0; i < 3; i++) { for (int j = 0; j < 3; j++) E.R[i][j] = est[i][j]; E.t[i] = est[i][3]; }
    double W = m.widthMM(), H = m.heightMM();
    const double pts[5][2] = {{0, 0}, {W, 0}, {W, H}, {0, H}, {W * 0.5, H * 0.5}};
    double sum = 0;
    for (auto &p : pts) {
        double x1, y1, x2, y2;
        projectMarkerPoint(gt, cam, p[0], p[1], x1, y1); projectMarkerPoint(E, cam, p[0], p[1], x2, y2);
        sum += std::hypot(x1 - x2, y1 - y2);
    }
    PoseError e; e.cornerPx = sum / 5.0;
    // Compare marker-centre position in camera space.
    double cg[3], ce[3];
    for (int i = 0; i < 3; i++) {
        cg[i] = gt.R[i][0] * W * 0.5 + gt.R[i][1] * H * 0.5 + gt.t[i];
        ce[i] = E.R[i][0] * W * 0.5 + E.R[i][1] * H * 0.5 + E.t[i];
    }
    e.transMM = std::sqrt((cg[0] - ce[0]) * (cg[0] - ce[0]) + (cg[1] - ce[1]) * (cg[1] - ce[1]) + (cg[2] - ce[2]) * (cg[2] - ce[2]));
    e.transRel = e.transMM / std::sqrt(cg[0] * cg[0] + cg[1] * cg[1] + cg[2] * cg[2]);
    double tr = 0; for (int i = 0; i < 3; i++) for (int k = 0; k < 3; k++) tr += E.R[k][i] * gt.R[k][i];  // trace(E^T * G)
    e.rotDeg = std::acos(std::min(1.0, std::max(-1.0, (tr - 1.0) / 2.0))) * 180.0 / kPi;
    return e;
}

double now_ms() {
    using namespace std::chrono;
    return duration<double, std::milli>(steady_clock::now().time_since_epoch()).count();
}

double percentile(std::vector<double> v, double p) {
    if (v.empty()) return NAN;
    std::sort(v.begin(), v.end());
    double idx = p * (v.size() - 1); size_t i = (size_t)idx; double f = idx - i;
    return i + 1 < v.size() ? v[i] * (1 - f) + v[i + 1] * f : v[i];
}

// ------------------------------------------------------------------------------------------------
// Engine wrapper (KPM + AR2)
// ------------------------------------------------------------------------------------------------
struct Engine {
    ARParam cparam; ARParamLT *lt = NULL; KpmHandle *kpm = NULL; AR2HandleT *ar2 = NULL; AR2SurfaceSetT *surf = NULL;
    Camera cam;

    bool init(const char *dataset, int w, int h, double fovyDeg, int kpmProc, int threads) {
        cam.w = w; cam.h = h;
        arParamClearWithFOVy(&cparam, w, h, deg2rad(fovyDeg));
        cam.fx = cparam.mat[0][0]; cam.fy = cparam.mat[1][1]; cam.cx = cparam.mat[0][2]; cam.cy = cparam.mat[1][2];
        lt = arParamLTCreate(&cparam, AR_PARAM_LT_DEFAULT_OFFSET);
        if (!lt) return false;
        kpm = kpmCreateHandle(lt);
        if (!kpm) return false;
        kpmSetProcMode(kpm, (KPM_PROC_MODE)kpmProc);
        KpmRefDataSet *ref = NULL;
        if (kpmLoadRefDataSet(dataset, "fset3", &ref) < 0) { fprintf(stderr, "Cannot load %s.fset3\n", dataset); return false; }
        if (kpmChangePageNoOfRefDataSet(ref, KpmChangePageNoAllPages, 0) < 0) return false;
        if (kpmSetRefDataSet(kpm, ref) < 0) return false;
        kpmDeleteRefDataSet(&ref);
        ar2 = ar2CreateHandle(lt, AR_PIXEL_FORMAT_MONO, threads);
        if (!ar2) return false;
        ar2SetTrackingThresh(ar2, 5.0); ar2SetSimThresh(ar2, 0.50); ar2SetSearchFeatureNum(ar2, 16);
        ar2SetSearchSize(ar2, 12); ar2SetTemplateSize1(ar2, 6); ar2SetTemplateSize2(ar2, 6);
        surf = ar2ReadSurfaceSet(dataset, "fset", NULL);
        if (!surf) { fprintf(stderr, "Cannot load %s.fset\n", dataset); return false; }
        return true;
    }
    // Returns true and fills pose/inliers if a page was detected.
    bool detect(const std::vector<uint8_t> &frame, float pose[3][4], int *inliers, double *ms) {
        double t0 = now_ms();
        kpmMatching(kpm, const_cast<ARUint8 *>(frame.data()));
        *ms = now_ms() - t0;
        KpmResult *res = NULL; int n = 0;
        kpmGetResult(kpm, &res, &n);
        bool found = false; float best = 1e30f;
        for (int i = 0; i < n; i++) {
            if (res[i].camPoseF != 0) continue;
            if (!found || res[i].error < best) {
                found = true; best = res[i].error; *inliers = res[i].inlierNum;
                for (int r = 0; r < 3; r++) for (int c = 0; c < 4; c++) pose[r][c] = res[i].camPose[r][c];
            }
        }
        return found;
    }
    ~Engine() {
        if (ar2) ar2DeleteHandle(&ar2);
        if (surf) ar2FreeSurfaceSet(&surf);
        if (kpm) kpmDeleteHandle(&kpm);
        if (lt) arParamLTFree(&lt);
    }
};

// ------------------------------------------------------------------------------------------------
// Scenarios
// ------------------------------------------------------------------------------------------------
struct Level2 { std::string label; double value; };
struct Scenario { std::string name; std::vector<double> values; };

PoseSpec nominalSpec(Rng &rng) {
    PoseSpec s; s.distFactor = rng.uni(1.2, 1.8); s.tiltDeg = rng.uni(0, 20); s.tiltAzimuthDeg = rng.uni(0, 360);
    s.rollDeg = rng.uni(-30, 30); s.dxFrac = rng.uni(-0.12, 0.12); s.dyFrac = rng.uni(-0.12, 0.12);
    return s;
}

void applyScenario(const std::string &name, double v, PoseSpec &s, Degrade &d) {
    if (name == "scale") s.distFactor = v;
    else if (name == "tilt") s.tiltDeg = v;
    else if (name == "roll") s.rollDeg = v;
    else if (name == "blur") d.blurSigma = v;
    else if (name == "noise") d.noiseSigma = v;
    else if (name == "light") { d.gain = v; d.offset = (v < 1.0 ? -10.0 * (1.0 - v) / 0.3 : 0.0); d.ramp = (v < 1.0 ? 0.3 : 0.0); }
    else if (name == "occlusion") d.occlusion = v;
}

std::vector<Scenario> allScenarios() {
    return {
        {"scale", {1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0}},
        {"tilt", {0, 15, 30, 45, 55, 65, 72, 78}},
        {"roll", {0, 45, 90, 135, 180}},
        {"blur", {0, 1, 2, 3, 4}},
        {"noise", {0, 5, 10, 20, 30}},
        {"light", {1.0, 0.7, 0.4, 0.25}},
        {"occlusion", {0, 0.2, 0.4, 0.6}},
    };
}

std::map<std::string, std::string> parseArgs(int argc, char **argv) {
    std::map<std::string, std::string> a;
    for (int i = 1; i < argc; i++) { std::string s = argv[i]; size_t e = s.find('='); if (e != std::string::npos) a[s.substr(0, e)] = s.substr(e + 1); }
    return a;
}

}  // namespace

int main(int argc, char **argv) {
    auto args = parseArgs(argc, argv);
    auto get = [&](const char *k, const char *def) { auto it = args.find(k); return it == args.end() ? std::string(def) : it->second; };
    if (!args.count("dataset") || !args.count("image")) {
        fprintf(stderr, "usage: nft_eval dataset=<path/noext> image=<marker.jpg> dpi=<float> [mode=detect|track|all] [trials=10] [seqlen=90]\n"
                        "                [width=640 height=480 fovy=45 seed=1 scenarios=a,b kpm_proc=1 threads=1 csv=out.csv]\n");
        return 2;
    }
    const std::string mode = get("mode", "all");
    const int trials = atoi(get("trials", "10").c_str()), seqlen = atoi(get("seqlen", "90").c_str());
    const int W = atoi(get("width", "640").c_str()), H = atoi(get("height", "480").c_str());
    const double fovy = atof(get("fovy", "45").c_str()), dpi = atof(get("dpi", "150").c_str());
    const uint64_t seed = (uint64_t)atoll(get("seed", "1").c_str());
    const int kpmProc = atoi(get("kpm_proc", "1").c_str()), threads = atoi(get("threads", "1").c_str());
    const double okPx = atof(get("ok_px", "5").c_str());   // a pose within this mean corner error counts as correct
    arLogLevel = AR_LOG_LEVEL_ERROR; setvbuf(stdout, NULL, _IONBF, 0);

    Marker marker;
    if (!loadMarker(args["image"].c_str(), dpi, marker)) return 1;
    Engine eng;
    if (!eng.init(args["dataset"].c_str(), W, H, fovy, kpmProc, threads)) return 1;
    printf("# nft_eval  marker %dx%d px @%.1f dpi = %.1f x %.1f mm | frame %dx%d fovy %.1f f=%.1f | kpm_proc=%d | %s\n",
           marker.pyr[0].w, marker.pyr[0].h, dpi, marker.widthMM(), marker.heightMM(), W, H, fovy, eng.cam.fx, kpmProc,
#if defined(_MSC_VER)
           "MSVC"
#elif defined(__clang__)
           "clang"
#else
           "gcc"
#endif
    );

    FILE *csv = NULL;
    if (args.count("csv")) {
        csv = fopen(args["csv"].c_str(), "w");
        if (csv) fprintf(csv, "kind,scenario,level,trial,frame,found,corner_px,trans_mm,trans_rel,rot_deg,inliers,detect_ms,track_ms\n");
    }

    std::vector<std::string> want;
    { std::string s = get("scenarios", ""); size_t p = 0; while (p < s.size()) { size_t e = s.find(',', p); if (e == std::string::npos) e = s.size(); want.push_back(s.substr(p, e - p)); p = e + 1; } }
    std::vector<Scenario> scen;
    for (auto &sc : allScenarios()) if (want.empty() || std::find(want.begin(), want.end(), sc.name) != want.end()) scen.push_back(sc);

    // ---------------------------------------------------------------- detection ----
    if (mode == "detect" || mode == "all") {
        printf("\n== KPM detection (%d trials / level) ==\n", trials);
        printf("%-10s %8s | %6s %7s | %9s %9s | %8s %8s | %9s\n", "scenario", "level", "found%", "ok%", "med_px", "p90_px", "med_mm", "med_deg", "det_ms");
        for (auto &sc : scen) for (double lv : sc.values) {
            int found = 0, ok = 0; std::vector<double> px, mm, dg, ms;
            for (int t = 0; t < trials; t++) {
                Rng rng(seed * 1000003ull + (uint64_t)(std::hash<std::string>()(sc.name) % 9973) * 7919ull + (uint64_t)(lv * 1000) * 31ull + t);
                PoseSpec ps = nominalSpec(rng); Degrade d; applyScenario(sc.name, lv, ps, d);
                Pose gt = makePose(ps, marker, eng.cam);
                std::vector<float> bg = makeBackground(eng.cam, rng, d.bgContrast);
                std::vector<uint8_t> frame; renderFrame(marker, eng.cam, {gt}, bg, d, rng, frame);
                float pose[3][4]; int inl = 0; double dms = 0;
                bool f = eng.detect(frame, pose, &inl, &dms);
                ms.push_back(dms);
                PoseError e = {0, 0, 0, 0};
                if (f) { found++; e = comparePose(gt, pose, marker, eng.cam); if (e.cornerPx < okPx) { ok++; px.push_back(e.cornerPx); mm.push_back(e.transMM); dg.push_back(e.rotDeg); } }
                if (csv) fprintf(csv, "detect,%s,%g,%d,0,%d,%.3f,%.3f,%.5f,%.3f,%d,%.2f,\n", sc.name.c_str(), lv, t, f, e.cornerPx, e.transMM, e.transRel, e.rotDeg, inl, dms);
            }
            printf("%-10s %8g | %5.0f%% %6.0f%% | %9.2f %9.2f | %8.2f %8.2f | %9.1f\n", sc.name.c_str(), lv, 100.0 * found / trials,
                   100.0 * ok / trials, percentile(px, 0.5), percentile(px, 0.9), percentile(mm, 0.5), percentile(dg, 0.5), percentile(ms, 0.5));
            fflush(stdout);
        }
    }

    // ----------------------------------------------------------------- tracking ----
    if (mode == "track" || mode == "all") {
        printf("\n== NFT tracking: KPM init + AR2 tracking, %d frames/sequence, %d sequences/level ==\n", seqlen, std::max(1, trials / 3));
        printf("%-10s %8s | %7s %7s | %9s %9s | %6s %6s | %8s %8s\n", "scenario", "px/frame", "valid%", "ok%", "med_px", "p90_px", "lost", "inits", "trk_ms", "det_ms");
        const double speeds[] = {0, 2, 5, 10, 20, 35};
        const int nseq = std::max(1, trials / 3);
        for (double v : speeds) {
            long frames = 0, validF = 0, okF = 0, lostEv = 0, inits = 0; std::vector<double> px, trk, det;
            for (int q = 0; q < nseq; q++) {
                Rng rng(seed * 7777777ull + (uint64_t)(v * 100) * 131ull + q);
                PoseSpec base = nominalSpec(rng); base.distFactor = rng.uni(1.3, 1.7); base.tiltDeg = rng.uni(5, 25);
                double dirx = std::cos(rng.uni(0, 2 * kPi)), diry = std::sin(rng.uni(0, 2 * kPi));
                double omega = v * 0.15;  // deg/frame, roll
                Degrade d; d.noiseSigma = 3.0; d.blurSigma = 0.6;
                std::vector<float> bg = makeBackground(eng.cam, rng, 1.0);
                bool tracking = false; float trans[3][4];
                // Reset AR2 internal state by re-initialising on each sequence (init pose is set on detection).
                for (int f = 0; f < seqlen; f++) {
                    auto specAt = [&](double fr) {
                        PoseSpec s = base;
                        // Triangle-wave motion keeps the marker inside the frame at any speed.
                        auto tri = [](double x) { double m = std::fmod(x, 4.0); if (m < 0) m += 4.0; return m < 1 ? m : (m < 3 ? 2 - m : m - 4); };
                        double dpx = v * fr;
                        s.dxFrac = base.dxFrac + 0.28 * tri(dirx * dpx / (0.28 * W) * 1.0 + 0.0);
                        s.dyFrac = base.dyFrac + 0.28 * tri(diry * dpx / (0.28 * H) * 1.0);
                        s.rollDeg = base.rollDeg + omega * fr;
                        s.tiltDeg = base.tiltDeg + 8.0 * std::sin(fr * 0.05 * (1.0 + v * 0.05));
                        return s;
                    };
                    int sub = 1 + std::min(6, (int)(v / 3.0));   // motion blur: average over half a frame interval
                    std::vector<Pose> poses;
                    for (int k = 0; k < sub; k++) poses.push_back(makePose(specAt(f + (sub == 1 ? 0.0 : (k / (double)(sub - 1) - 0.5) * 0.5)), marker, eng.cam));
                    Pose gt = makePose(specAt(f), marker, eng.cam);
                    std::vector<uint8_t> frame; renderFrame(marker, eng.cam, poses, bg, d, rng, frame);

                    frames++; bool valid = false; float est[3][4]; double tms = 0, dms = 0; int inl = 0;
                    if (!tracking) {
                        if (eng.detect(frame, est, &inl, &dms)) {
                            inits++; tracking = true; valid = true; det.push_back(dms);
                            memcpy(trans, est, sizeof(trans)); ar2SetInitTrans(eng.surf, trans);
                        } else det.push_back(dms);
                    } else {
                        float err = 0; double t0 = now_ms();
                        int rc = ar2Tracking(eng.ar2, eng.surf, const_cast<ARUint8 *>(frame.data()), trans, &err);
                        tms = now_ms() - t0; trk.push_back(tms);
                        if (rc < 0) { tracking = false; lostEv++; } else { valid = true; memcpy(est, trans, sizeof(est)); }
                    }
                    PoseError e = {0, 0, 0, 0};
                    if (valid) { validF++; e = comparePose(gt, est, marker, eng.cam); if (e.cornerPx < okPx) { okF++; px.push_back(e.cornerPx); } else { tracking = false; lostEv++; } }
                    if (csv) fprintf(csv, "track,speed,%g,%d,%d,%d,%.3f,%.3f,%.5f,%.3f,%d,%.2f,%.2f\n", v, q, f, valid, e.cornerPx, e.transMM, e.transRel, e.rotDeg, inl, dms, tms);
                }
            }
            printf("%-10s %8g | %6.0f%% %6.0f%% | %9.2f %9.2f | %6ld %6ld | %8.1f %8.1f\n", "speed", v, 100.0 * validF / frames, 100.0 * okF / frames,
                   percentile(px, 0.5), percentile(px, 0.9), lostEv, inits, percentile(trk, 0.5), percentile(det, 0.5));
            fflush(stdout);
        }
    }
    if (csv) fclose(csv);
    return 0;
}
