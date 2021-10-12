val spinalVersion = "1.6.0"

lazy val root = (project in file(".")).
  settings(
    inThisBuild(List(
      organization := "com.github.spinalhdl",
      scalaVersion := "2.11.12",
      version      := "0.1.0-SNAPSHOT"
    )),
    name := "VexRiscvOnWishbone",
    libraryDependencies ++= Seq(
        compilerPlugin("com.github.spinalhdl" % "spinalhdl-idsl-plugin_2.11" % spinalVersion)
    ),
    scalacOptions += s"-Xplugin-require:idsl-plugin"
  ).dependsOn(vexRiscv)


//
// Perhaps we should use $CFU_ROOT, sys.env.get("CFU_ROOT")
//
lazy val vexRiscv = RootProject(file("../../third_party/python/pythondata_cpu_vexriscv/pythondata_cpu_vexriscv/verilog/ext/VexRiscv"))
fork := true
