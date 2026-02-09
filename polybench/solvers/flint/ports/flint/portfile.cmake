vcpkg_download_distfile(ARCHIVE
    URLS "https://github.com/flintlib/flint/releases/download/v${VERSION}/flint-${VERSION}.tar.xz"
    FILENAME "flint-${VERSION}.tar.xz"
    SHA512 f7f0ee7837d960c64b207d542fa384d6b3ab923c5d218d6545c4cd8abd0efd56c99e88a72b837e966127e0b6d3d42a3bf53ed947df89ecaa004377431f060a78
)

vcpkg_extract_source_archive(
    SOURCE_PATH
    ARCHIVE "${ARCHIVE}"
)

set(_extra_libs "")
if(VCPKG_TARGET_IS_LINUX)
    set(_extra_libs "LIBS=-lm")
endif()

vcpkg_configure_make(
    SOURCE_PATH "${SOURCE_PATH}"
    AUTOCONFIG
    OPTIONS ${_extra_libs}
)

vcpkg_install_make()
vcpkg_copy_pdbs()
vcpkg_fixup_pkgconfig()

vcpkg_install_copyright(
    FILE_LIST "${SOURCE_PATH}/COPYING" "${SOURCE_PATH}/COPYING.LESSER"
)
