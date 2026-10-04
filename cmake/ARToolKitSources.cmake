#
#  ARToolKitSources.cmake
#  artoolkit-nft-bench
#
#  This file is part of artoolkit-nft-bench.
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  Copyright 2026 WebARKit.
#
#  Author(s): Walter Perdan @kalwalt https://github.com/kalwalt
#

# Generated from extern/artoolkit5/VisualStudio/vs2017/*.vcxproj (the authoritative Windows source sets).
# Paths are relative to the artoolkit5 submodule root (ARTK5_ROOT).

set(ARTK5_AR_SOURCES
    ${ARTK5_ROOT}/lib/SRC/AR/ar3DCreateHandle.c
    ${ARTK5_ROOT}/lib/SRC/AR/ar3DUtil.c
    ${ARTK5_ROOT}/lib/SRC/AR/arCreateHandle.c
    ${ARTK5_ROOT}/lib/SRC/AR/arDetectMarker.c
    ${ARTK5_ROOT}/lib/SRC/AR/arDetectMarker2.c
    ${ARTK5_ROOT}/lib/SRC/AR/arFilterTransMat.c
    ${ARTK5_ROOT}/lib/SRC/AR/arGetLine.c
    ${ARTK5_ROOT}/lib/SRC/AR/arGetMarkerInfo.c
    ${ARTK5_ROOT}/lib/SRC/AR/arGetTransMat.c
    ${ARTK5_ROOT}/lib/SRC/AR/arGetTransMatStereo.c
    ${ARTK5_ROOT}/lib/SRC/AR/arImageProc.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabeling.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubDBIC.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubDBRC.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubDBZ.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubDWIC.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubDWRC.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubDWZ.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubEBIC.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubEBRC.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubEBZ.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubEWIC.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubEWRC.c
    ${ARTK5_ROOT}/lib/SRC/AR/arLabelingSub/arLabelingSubEWZ.c
    ${ARTK5_ROOT}/lib/SRC/AR/arPattAttach.c
    ${ARTK5_ROOT}/lib/SRC/AR/arPattCreateHandle.c
    ${ARTK5_ROOT}/lib/SRC/AR/arPattGetID.c
    ${ARTK5_ROOT}/lib/SRC/AR/arPattLoad.c
    ${ARTK5_ROOT}/lib/SRC/AR/arPattSave.c
    ${ARTK5_ROOT}/lib/SRC/AR/arUtil.c
    ${ARTK5_ROOT}/lib/SRC/AR/mAlloc.c
    ${ARTK5_ROOT}/lib/SRC/AR/mAllocDup.c
    ${ARTK5_ROOT}/lib/SRC/AR/mAllocInv.c
    ${ARTK5_ROOT}/lib/SRC/AR/mAllocMul.c
    ${ARTK5_ROOT}/lib/SRC/AR/mAllocTrans.c
    ${ARTK5_ROOT}/lib/SRC/AR/mAllocUnit.c
    ${ARTK5_ROOT}/lib/SRC/AR/mDet.c
    ${ARTK5_ROOT}/lib/SRC/AR/mDisp.c
    ${ARTK5_ROOT}/lib/SRC/AR/mDup.c
    ${ARTK5_ROOT}/lib/SRC/AR/mFree.c
    ${ARTK5_ROOT}/lib/SRC/AR/mInv.c
    ${ARTK5_ROOT}/lib/SRC/AR/mMul.c
    ${ARTK5_ROOT}/lib/SRC/AR/mPCA.c
    ${ARTK5_ROOT}/lib/SRC/AR/mSelfInv.c
    ${ARTK5_ROOT}/lib/SRC/AR/mTrans.c
    ${ARTK5_ROOT}/lib/SRC/AR/mUnit.c
    ${ARTK5_ROOT}/lib/SRC/AR/paramChangeSize.c
    ${ARTK5_ROOT}/lib/SRC/AR/paramClear.c
    ${ARTK5_ROOT}/lib/SRC/AR/paramDecomp.c
    ${ARTK5_ROOT}/lib/SRC/AR/paramDisp.c
    ${ARTK5_ROOT}/lib/SRC/AR/paramDistortion.c
    ${ARTK5_ROOT}/lib/SRC/AR/paramFile.c
    ${ARTK5_ROOT}/lib/SRC/AR/paramGL.c
    ${ARTK5_ROOT}/lib/SRC/AR/paramGetPerspective.c
    ${ARTK5_ROOT}/lib/SRC/AR/paramLT.c
    ${ARTK5_ROOT}/lib/SRC/AR/vAlloc.c
    ${ARTK5_ROOT}/lib/SRC/AR/vDisp.c
    ${ARTK5_ROOT}/lib/SRC/AR/vFree.c
    ${ARTK5_ROOT}/lib/SRC/AR/vHouse.c
    ${ARTK5_ROOT}/lib/SRC/AR/vInnerP.c
    ${ARTK5_ROOT}/lib/SRC/AR/vTridiag.c
)

set(ARTK5_AR2_SOURCES
    ${ARTK5_ROOT}/lib/SRC/AR2/coord.c
    ${ARTK5_ROOT}/lib/SRC/AR2/featureMap.c
    ${ARTK5_ROOT}/lib/SRC/AR2/featureSet.c
    ${ARTK5_ROOT}/lib/SRC/AR2/handle.c
    ${ARTK5_ROOT}/lib/SRC/AR2/imageSet.c
    ${ARTK5_ROOT}/lib/SRC/AR2/jpeg.c
    ${ARTK5_ROOT}/lib/SRC/AR2/marker.c
    ${ARTK5_ROOT}/lib/SRC/AR2/matching.c
    ${ARTK5_ROOT}/lib/SRC/AR2/matching2.c
    ${ARTK5_ROOT}/lib/SRC/AR2/searchPoint.c
    ${ARTK5_ROOT}/lib/SRC/AR2/selectTemplate.c
    ${ARTK5_ROOT}/lib/SRC/AR2/surface.c
    ${ARTK5_ROOT}/lib/SRC/AR2/template.c
    ${ARTK5_ROOT}/lib/SRC/AR2/tracking.c
    ${ARTK5_ROOT}/lib/SRC/AR2/tracking2d.c
    ${ARTK5_ROOT}/lib/SRC/AR2/util.c
)

set(ARTK5_ARICP_SOURCES
    ${ARTK5_ROOT}/lib/SRC/ARICP/icpCalibStereo.c
    ${ARTK5_ROOT}/lib/SRC/ARICP/icpCore.c
    ${ARTK5_ROOT}/lib/SRC/ARICP/icpHandle.c
    ${ARTK5_ROOT}/lib/SRC/ARICP/icpPoint.c
    ${ARTK5_ROOT}/lib/SRC/ARICP/icpPointRobust.c
    ${ARTK5_ROOT}/lib/SRC/ARICP/icpStereoHandle.c
    ${ARTK5_ROOT}/lib/SRC/ARICP/icpStereoPoint.c
    ${ARTK5_ROOT}/lib/SRC/ARICP/icpStereoPointRobust.c
    ${ARTK5_ROOT}/lib/SRC/ARICP/icpUtil.c
)

set(ARTK5_ARUTIL_SOURCES
    ${ARTK5_ROOT}/lib/SRC/ARUtil/crypt.c
    ${ARTK5_ROOT}/lib/SRC/ARUtil/file_utils.c
    ${ARTK5_ROOT}/lib/SRC/ARUtil/ioapi.c
    ${ARTK5_ROOT}/lib/SRC/ARUtil/log.c
    ${ARTK5_ROOT}/lib/SRC/ARUtil/nftw.c
    ${ARTK5_ROOT}/lib/SRC/ARUtil/profile.c
    ${ARTK5_ROOT}/lib/SRC/ARUtil/system.c
    ${ARTK5_ROOT}/lib/SRC/ARUtil/thread_sub.c
    ${ARTK5_ROOT}/lib/SRC/ARUtil/time.c
    ${ARTK5_ROOT}/lib/SRC/ARUtil/unzip.c
    ${ARTK5_ROOT}/lib/SRC/ARUtil/zip.c
)

set(ARTK5_KPM_SOURCES
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/detectors/DoG_scale_invariant_detector.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/detectors/gaussian_scale_space_pyramid.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/detectors/gradients.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/detectors/harris.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/detectors/orientation_assignment.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/detectors/pyramid.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/facade/visual_database_facade.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/framework/date_time.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/framework/image.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/framework/logger.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/framework/timers.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/matchers/freak.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher/matchers/hough_similarity_voting.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/kpmFopen.c
    ${ARTK5_ROOT}/lib/SRC/KPM/kpmHandle.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/kpmMatching.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/kpmRefDataSet.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/kpmResult.cpp
    ${ARTK5_ROOT}/lib/SRC/KPM/kpmUtil.cpp
)
