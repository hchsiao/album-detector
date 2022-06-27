def testdata_genrule(name, album_dirs):
  native.genrule(
    name = name,
    srcs = [],
    outs = ["testdata.json"],
    cmd = "./$(location mktestdata) --output $@ --album-dirs %s" % ' '.join(album_dirs),
    tools = [":mktestdata"],
    visibility = ["//visibility:public"],
  )
