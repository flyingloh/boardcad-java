"C:\Program Files\Java\jdk-11.0.2\bin\javac" -cp gluegen-rt.jar;j3dcore.jar;j3dutils.jar;jogl-all.jar;vecmath.jar;jython.jar;Lib.jar;jythonconsole.jar;.\BoardCAD.jar .\boardcad\gui\jdk\BoardCAD.java
pause
"C:\Program Files\Java\jdk-11.0.2\bin\jar" ufv BoardCAD.jar .\boardcad\gui\jdk\BoardCAD*.class .\boardcad\gui\jdk\BoardHandler*.class .\boardcad\gui\jdk\JOGLPanel*.class .\boardcad\gui\jdk\DesignPanel*.class .\boardcad\gui\jdk\ThreeDView*.class .\board\BezierBoard*.class .\board\NurbsBoard*.class .\boardcam\cutters\STLCutter*.class .\boardcad\export\DxfExport*.class .\board\readers\S3dReader*.class
pause

REM -Xlint:unchecked -Xlint:deprecation