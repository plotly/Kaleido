executable("kaleido") {
  sources = [ "app/kaleido.cc" ]

  deps = [
    ":headless_shell_lib",
    "//skia",
  ]
}