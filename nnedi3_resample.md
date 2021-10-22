### Requirements
[nnedi3](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-EEDI3) [fmtconv](https://github.com/EleonoreMizo/fmtconv/) [mvsfunc](https://github.com/HomeOfVapourSynthEvolution/mvsfunc)

### Usage
Put nnedi3_resample.py into `<python folder>\Lib\site-packages\vapoursynth`

### Function
It can do scaling, color space conversion, etc.

### Note
Internally always processing in 16-bit integer, and the output format can be specified by "csp" with Format id (default is the same as input).

### Example
Double the width and height of a clip.

```Python
import vapoursynth as vs
import nnedi3_resample as nnrs

core = vs.core

clip = XXXSource()
clip = nnrs.nnedi3_resample(clip, clip.width * 2, clip.height * 2)

clip.set_output()
```