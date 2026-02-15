{ pkgs }: {
  deps = [
    pkgs.python3
    pkgs.nodejs-20_x
    pkgs.nodePackages.typescript-language-server
    pkgs.nodePackages.pnpm
    pkgs.util-linux
  ];
}
