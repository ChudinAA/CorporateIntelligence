{pkgs}: {
  deps = [
    pkgs.wget
    pkgs.iana-etc
    pkgs.glibcLocales
    pkgs.postgresql
    pkgs.openssl
  ];
}
