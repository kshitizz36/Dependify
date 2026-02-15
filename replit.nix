{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.nodejs-20_x
    pkgs.nodePackages.typescript-language-server
    pkgs.nodePackages.pnpm
    pkgs.libuuid
  ];
}
