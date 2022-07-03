def testdata_genrule(name, album_dirs):
  mktestdata = "//tests/tools:mktestdata"
  native.genrule(
    name = name,
    srcs = [],
    outs = ["testdata.json"],
    cmd = "./$(location %s) --output $@ --album-dirs %s" % (mktestdata, ' '.join(album_dirs)),
    tools = [mktestdata],
    visibility = ["//visibility:public"],
  )
