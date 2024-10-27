{pkgs}: {
  deps = [
    pkgs.chromedriver
    pkgs.chromium
    pkgs.geckodriver
    pkgs.openblas
    pkgs.file
    pkgs.glibcLocales
    pkgs.postgresql
  ];
}
