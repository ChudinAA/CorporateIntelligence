{pkgs}: {
  deps = [
    pkgs.bash
    pkgs.wget
    pkgs.iana-etc
    pkgs.glibcLocales
    pkgs.postgresql
    pkgs.openssl
  ];
}
