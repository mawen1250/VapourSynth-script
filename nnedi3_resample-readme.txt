Requirements: nnedi3, fmtconv, havsfunc
Usage: Put nnedi3_resample.py into <python folder>\Lib\site-packages\
Function: It can do scaling, color space conversion, etc.
Note: Internally always processing in 16-bit integer, and it always output 16-bit integer clip.

Example
Double the width and height of clip.

    import vapoursynth as vs
    import nnedi3_resample as nnrs
    
    core = vs.get_core()
    
    clip = XXXSource()
    clip = nnrs.nnedi3_resample(clip, clip.width * 2, clip.height * 2)
    
    clip.set_output()
