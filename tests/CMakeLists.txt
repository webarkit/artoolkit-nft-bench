# Headless NFT quality harness (synthetic frames with ground-truth pose).
add_executable(nft_eval nft_eval.cpp)
target_link_libraries(nft_eval PRIVATE KPM AR2 ARICP AR ARUtil JPEG::JPEG)
if(MSVC)
    target_compile_definitions(nft_eval PRIVATE _CRT_SECURE_NO_WARNINGS _USE_MATH_DEFINES NOMINMAX)
    target_compile_options(nft_eval PRIVATE /W3 /wd4244 /wd4267 /wd4305 /wd4996)
endif()
set_target_properties(nft_eval PROPERTIES FOLDER "tests")
