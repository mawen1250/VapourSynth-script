import vapoursynth as vs
import havsfunc as haf
import mvsfunc as mvf
import math


def nnedi3_resample(input, target_width=None, target_height=None, src_left=None, src_top=None, src_width=None, src_height=None, csp=None, mats=None, matd=None, cplaces=None, cplaced=None, fulls=None, fulld=None, curves=None, curved=None, sigmoid=None, scale_thr=None, nsize=None, nns=None, qual=None, etype=None, pscrn=None, opt=None, fapprox=None, kernel=None, invks=False, taps=None, invkstaps=3, a1=None, a2=None, chromak_up=None, chromak_up_taps=None, chromak_up_a1=None, chromak_up_a2=None, chromak_down=None, chromak_down_invks=False, chromak_down_invkstaps=3, chromak_down_taps=None, chromak_down_a1=None, chromak_down_a2=None, fast=None):
    core = vs.get_core()
    funcName = 'nnedi3_resample'
    
    # Get property about input clip
    if not isinstance(input, vs.VideoNode):
        raise ValueError(funcName + ': This is not a clip!')
    
    sFormat = input.format
    
    sColorFamily = sFormat.color_family
    if sColorFamily == vs.COMPAT:
        raise ValueError(funcName + ': Color family *COMPAT* of input clip is not supported!')
    sIsGRAY = sColorFamily == vs.GRAY
    sIsYUV = sColorFamily == vs.YUV or sColorFamily == vs.YCOCG
    sIsRGB = sColorFamily == vs.RGB
    
    sbitPS = sFormat.bits_per_sample
    
    sHSubS = 1 << sFormat.subsampling_w
    sVSubS = 1 << sFormat.subsampling_h
    sIsSubS = sHSubS > 1 or sVSubS > 1
    
    sPlaneNum = sFormat.num_planes
    
    # Get property about output clip
    dFormat = sFormat if csp is None else core.get_format(csp)
    
    dColorFamily = dFormat.color_family
    if dColorFamily == vs.COMPAT:
        raise ValueError(funcName + ': Color family *COMPAT* of output clip is not supported!')
    dIsGRAY = dColorFamily == vs.GRAY
    dIsYUV = dColorFamily == vs.YUV or dColorFamily == vs.YCOCG
    dIsRGB = dColorFamily == vs.RGB
    
    dbitPS = dFormat.bits_per_sample
    
    dHSubS = 1 << dFormat.subsampling_w
    dVSubS = 1 << dFormat.subsampling_h
    dIsSubS = dHSubS > 1 or dVSubS > 1
    
    dPlaneNum = dFormat.num_planes
    
    # Parameters of format
    SD = input.width <= 1024 and input.height <= 576
    HD = input.width <= 2048 and input.height <= 1536
    
    if mats is None:
        mats = "601" if SD else "709" if HD else "2020"
    else:
        mats = mats.lower()
    if matd is None:
        matd = mats
    else:
        matd = matd.lower()
        # Matrix of output clip makes sense only if dst is not of RGB
        if dIsRGB:
            matd = mats
        # Matrix of input clip makes sense only src is not of GRAY or RGB
        if sIsGRAY or sIsRGB:
            mats = matd
    if cplaces is None:
        if sHSubS == 4:
            cplaces = 'dv'
        else:
            cplaces = 'mpeg2'
    else:
        cplaces = cplaces.lower()
    if cplaced is None:
        if dHSubS == 4:
            cplaced = 'dv'
        else:
            cplaced = cplaces
    else:
        cplaced = cplaced.lower()
    if fulls is None:
        fulls = sColorFamily == vs.YCOCG or sColorFamily == vs.RGB
    if fulld is None:
        if dColorFamily == sColorFamily:
            fulld = fulls
        else:
            fulld = dColorFamily == vs.YCOCG or dColorFamily == vs.RGB
    if curves is None:
        curves = 'linear'
    else:
        curves = curves.lower()
    if curved is None:
        curved = curves
    else:
        curved = curved.lower()
    if sigmoid is None:
        sigmoid = False
    
    # Parameters of scaling
    if target_width is None:
        target_width = input.width
    if target_height is None:
        target_height = input.height
    if src_left is None:
        src_left = 0
    if src_top is None:
        src_top = 0
    if src_width is None:
        src_width = input.width
    elif src_width <= 0:
        src_width = input.width - src_left + src_width
    if src_height is None:
        src_height = input.height
    elif src_height <= 0:
        src_height = input.height - src_top + src_height
    if scale_thr is None:
        scale_thr = 1.125
    
    src_right = src_width - input.width + src_left
    src_bottom = src_height - input.height + src_top
    
    hScale = target_width / src_width
    vScale = target_height / src_height
    
    # Parameters of nnedi3
    if nsize is None:
        nsize = 0
    if nns is None:
        nns = 3
    if qual is None:
        qual = 2
    
    # Parameters of fmtc.resample
    if kernel is None:
        if not invks:
            kernel = 'spline36'
        else:
            kernel = 'bilinear'
    else:
        kernel = kernel.lower()
    if chromak_up is None:
        chromak_up = 'nnedi3'
    else:
        chromak_up = chromak_up.lower()
    if chromak_up == 'softcubic':
        chromak_up = 'bicubic'
        if chromak_up_a1 is None:
            chromak_up_a1 = 75
        chromak_up_a1 = chromak_up_a1 / 100
        chromak_up_a2 = 1 - chromak_up_a1
    if chromak_down is None:
        chromak_down = 'bicubic'
    else:
        chromak_down = chromak_down.lower()
    if chromak_down == 'softcubic':
        chromak_down = 'bicubic'
        if chromak_down_a1 is None:
            chromak_down_a1 = 75
        chromak_down_a1 = chromak_down_a1 / 100
        chromak_down_a2 = 1 - chromak_down_a1
    
    # Procedure decision
    hIsScale = hScale != 1
    vIsScale = vScale != 1
    isScale = hIsScale or vIsScale
    hResample = hIsScale or int(src_left) != src_left or int(src_right) != src_right
    vResample = vIsScale or int(src_top) != src_top or int(src_bottom) != src_bottom
    resample = hResample or vResample
    hReSubS = dHSubS != sHSubS
    vReSubS = dVSubS != sVSubS
    reSubS = hReSubS or vReSubS
    sGammaConv = curves != 'linear'
    dGammaConv = curved != 'linear'
    gammaCorrection = (sGammaConv or dGammaConv) and resample
    scaleInGRAY = sIsGRAY or dIsGRAY
    scaleInYUV = not scaleInGRAY and mats == matd and not gammaCorrection and (reSubS or (sIsYUV and dIsYUV))
    scaleInRGB = not scaleInGRAY and not scaleInYUV
    # If matrix conversion or gamma correction is applied, scaling will be done in RGB. Otherwise, if at least one of input&output clip is RGB and no chroma subsampling is involved, scaling will be done in RGB.
    
    # Chroma placement relative to the frame center in luma scale
    sCLeftAlign = cplaces == 'mpeg2' or cplaces == 'dv'
    sHCPlace = 0 if not sCLeftAlign else 0.5 - sHSubS / 2
    sVCPlace = 0
    dCLeftAlign = cplaced == 'mpeg2' or cplaced == 'dv'
    dHCPlace = 0 if not dCLeftAlign else 0.5 - dHSubS / 2
    dVCPlace = 0
    
    # Convert depth to 16-bit
    last = core.fmtc.bitdepth(input, bits=16, fulls=fulls) if sbitPS != 16 else input
    
    # Color space conversion before scaling
    if scaleInGRAY and sIsYUV:
        if mats != matd:
            last = core.fmtc.matrix(last, mats=mats, matd=matd, fulls=fulls, fulld=fulld, col_fam=vs.GRAY, singleout=0)
        last = core.std.ShufflePlanes(last, [0], vs.GRAY)
    elif scaleInGRAY and sIsRGB:
        # Matrix conversion for output clip of GRAY
        last = core.fmtc.matrix(last, mat=matd, fulls=fulls, fulld=fulld, col_fam=vs.GRAY, singleout=0)
        fulls = fulld
    elif scaleInRGB and sIsYUV:
        # Chroma upsampling
        if sIsSubS:
            if chromak_up == 'nnedi3':
                # Separate planes
                Y = core.std.ShufflePlanes(last, [0], vs.GRAY)
                U = core.std.ShufflePlanes(last, [1], vs.GRAY)
                V = core.std.ShufflePlanes(last, [2], vs.GRAY)
                # Chroma up-scaling
                U = nnedi3_resample_kernel(U, Y.width, Y.height, -sHCPlace / sHSubS, -sVCPlace / sVSubS, None, None, 1, nsize, nns, qual, etype, pscrn, opt, fapprox, kernel, taps, a1, a2, fast=fast)
                V = nnedi3_resample_kernel(V, Y.width, Y.height, -sHCPlace / sHSubS, -sVCPlace / sVSubS, None, None, 1, nsize, nns, qual, etype, pscrn, opt, fapprox, kernel, taps, a1, a2, fast=fast)
                # Merge planes
                last = core.std.ShufflePlanes([Y, U, V], [0, 0, 0], last.format.color_family)
            else:
                last = core.fmtc.resample(last, kernel=chromak_up, taps=chromak_up_taps, a1=chromak_up_a1, a2=chromak_up_a2, css="444", fulls=fulls, cplaces=cplaces)
        # Matrix conversion
        if mats == '2020cl':
            last = core.fmtc.matrix2020cl(last, fulls)
        else:
            last = core.fmtc.matrix(last, mat=mats, fulls=fulls, fulld=True, col_fam=vs.RGB, singleout=-1)
        fulls = True
    elif scaleInYUV and sIsRGB:
        # Matrix conversion
        if matd == '2020cl':
            last = core.fmtc.matrix2020cl(last, fulld)
        else:
            last = core.fmtc.matrix(last, mat=matd, fulls=fulls, fulld=fulld, col_fam=vs.YUV, singleout=-1)
        fulls = fulld
    
    # Scaling
    if scaleInGRAY or scaleInRGB:
        if sGammaConv:
            last = haf.GammaToLinear(last, fulls, fulls, curves, sigmoid=sigmoid)
        last = nnedi3_resample_kernel(last, target_width, target_height, src_left, src_top, src_width, src_height, scale_thr, nsize, nns, qual, etype, pscrn, opt, fapprox, kernel, taps, a1, a2, invks, invkstaps, fast=fast)
        if dGammaConv:
            last = haf.LinearToGamma(last, fulls, fulls, curved, sigmoid=sigmoid)
    elif scaleInYUV:
        # Separate planes
        Y = core.std.ShufflePlanes(last, [0], vs.GRAY)
        U = core.std.ShufflePlanes(last, [1], vs.GRAY)
        V = core.std.ShufflePlanes(last, [2], vs.GRAY)
        # Scale Y
        Y = nnedi3_resample_kernel(Y, target_width, target_height, src_left, src_top, src_width, src_height, scale_thr, nsize, nns, qual, etype, pscrn, opt, fapprox, kernel, taps, a1, a2, fast=fast)
        # Scale UV
        dCw = target_width // dHSubS
        dCh = target_height // dVSubS
        dCsx = ((src_left - sHCPlace) * hScale + dHCPlace) / hScale / sHSubS
        dCsy = ((src_top - sVCPlace) * vScale + dVCPlace) / vScale / sVSubS
        dCsw = src_width / sHSubS
        dCsh = src_height / sVSubS
        U = nnedi3_resample_kernel(U, dCw, dCh, dCsx, dCsy, dCsw, dCsh, scale_thr, nsize, nns, qual, etype, pscrn, opt, fapprox, kernel, taps, a1, a2, fast=fast)
        V = nnedi3_resample_kernel(V, dCw, dCh, dCsx, dCsy, dCsw, dCsh, scale_thr, nsize, nns, qual, etype, pscrn, opt, fapprox, kernel, taps, a1, a2, fast=fast)
        # Merge planes
        last = core.std.ShufflePlanes([Y, U, V], [0, 0, 0], last.format.color_family)
    
    # Color space conversion after scaling
    if scaleInGRAY and dIsYUV:
        dCw = target_width // dHSubS
        dCh = target_height // dVSubS
        if dbitPS != 16 or fulld != fulls:
            last = core.fmtc.bitdepth(last, bits=dbitPS, fulls=fulls, fulld=fulld)
        blkUV = core.std.BlankClip(last, dCw, dCh, color=[1 << (dbitPS - 1)])
        last = core.std.ShufflePlanes([last, blkUV, blkUV], [0, 0, 0], dColorFamily)
    elif scaleInGRAY and dIsRGB:
        if dbitPS != 16 or fulld != fulls:
            last = core.fmtc.bitdepth(last, bits=dbitPS, fulls=fulls, fulld=fulld)
        last = core.std.ShufflePlanes([last, last, last], [0, 0, 0], dColorFamily)
    elif scaleInRGB and dIsYUV:
        # Matrix conversion
        if matd == '2020cl':
            last = core.fmtc.matrix2020cl(last, fulld)
        else:
            last = core.fmtc.matrix(last, mat=matd, fulls=fulls, fulld=fulld, col_fam=dColorFamily, singleout=-1)
        # Chroma subsampling
        if dIsSubS:
            dCSS = '411' if dHSubS == 4 else '420' if dVSubS == 2 else '422'
            last = core.fmtc.resample(last, kernel=chromak_down, taps=chromak_down_taps, a1=chromak_down_a1, a2=chromak_down_a2, css=dCSS, fulls=fulld, cplaced=cplaced, invks=chromak_down_invks, invkstaps=chromak_down_invkstaps, planes=[2,3,3])
        if dbitPS != 16:
            last = core.fmtc.bitdepth(last, bits=dbitPS, fulls=fulld)
    elif scaleInYUV and dIsRGB:
        # Matrix conversion
        if mats == '2020cl':
            last = core.fmtc.matrix2020cl(last, fulls)
        else:
            last = core.fmtc.matrix(last, mat=mats, fulls=fulls, fulld=True, col_fam=vs.RGB, singleout=-1)
        if dbitPS != 16 or fulld != True:
            last = core.fmtc.bitdepth(last, bits=dbitPS, fulls=True, fulld=fulld)
    elif dbitPS != 16 or fulld != fulls:
        last = core.fmtc.bitdepth(last, bits=dbitPS, fulls=fulls, fulld=fulld)
    
    # Output
    return last


def nnedi3_resample_kernel(input, target_width=None, target_height=None, src_left=None, src_top=None, src_width=None, src_height=None, scale_thr=None, nsize=None, nns=None, qual=None, etype=None, pscrn=None, opt=None, fapprox=None, kernel=None, taps=None, a1=None, a2=None, invks=False, invkstaps=3, fast=None):
    core = vs.get_core()
    
    # Parameters of scaling
    if target_width is None:
        target_width = input.width
    if target_height is None:
        target_height = input.height
    if src_left is None:
        src_left = 0
    if src_top is None:
        src_top = 0
    if src_width is None:
        src_width = input.width
    elif src_width <= 0:
        src_width = input.width - src_left + src_width
    if src_height is None:
        src_height = input.height
    elif src_height <= 0:
        src_height = input.height - src_top + src_height
    if scale_thr is None:
        scale_thr = 1.125
    
    src_right = src_width - input.width + src_left
    src_bottom = src_height - input.height + src_top
    
    hScale = target_width / src_width
    vScale = target_height / src_height
    
    # Parameters of nnedi3
    if nsize is None:
        nsize = 0
    if nns is None:
        nns = 3
    if qual is None:
        qual = 2
    
    # Parameters of fmtc.resample
    if kernel is None:
        kernel = 'spline36'
    else:
        kernel = kernel.lower()
    
    # Procedure decision
    hIsScale = hScale != 1
    vIsScale = vScale != 1
    isScale = hIsScale or vIsScale
    hResample = hIsScale or int(src_left) != src_left or int(src_right) != src_right
    vResample = vIsScale or int(src_top) != src_top or int(src_bottom) != src_bottom
    resample = hResample or vResample
    
    # Scaling
    last = input
    
    if hResample:
        last = core.std.Transpose(last)
        last = nnedi3_resample_kernel_vertical(last, target_width, src_left, src_width, scale_thr, nsize, nns, qual, etype, pscrn, opt, fapprox, kernel, taps, a1, a2, invks, invkstaps, fast)
        last = core.std.Transpose(last)
    if vResample:
        last = nnedi3_resample_kernel_vertical(last, target_height, src_top, src_height, scale_thr, nsize, nns, qual, etype, pscrn, opt, fapprox, kernel, taps, a1, a2, invks, invkstaps, fast)
    
    # Output
    return last


def nnedi3_resample_kernel_vertical(input, target_height=None, src_top=None, src_height=None, scale_thr=None, nsize=None, nns=None, qual=None, etype=None, pscrn=None, opt=None, fapprox=None, kernel=None, taps=None, a1=None, a2=None, invks=False, invkstaps=3, fast=None):
    core = vs.get_core()
    
    # Parameters of scaling
    if target_height is None:
        target_height = input.height
    if src_top is None:
        src_top = 0
    if src_height is None:
        src_height = input.height
    elif src_height <= 0:
        src_height = input.height - src_top + src_height
    if scale_thr is None:
        scale_thr = 1.125
    
    scale = target_height / src_height # Total scaling ratio
    eTimes = math.ceil(math.log(scale / scale_thr, 2)) if scale > scale_thr else 0 # Iterative times of nnedi3
    eScale = 1 << eTimes # Scaling ratio of nnedi3
    pScale = scale / eScale # Scaling ratio of fmtc.resample
    
    # Parameters of nnedi3
    if nsize is None:
        nsize = 0
    if nns is None:
        nns = 3
    if qual is None:
        qual = 2
    
    # Parameters of fmtc.resample
    if kernel is None:
        kernel = 'spline36'
    else:
        kernel = kernel.lower()
    
    # Skip scaling if not needed
    if scale == 1 and src_top == 0 and src_height == input.height:
        return input
    
    # Scaling with nnedi3
    last = nnedi3_rpow2_vertical(input, eTimes, 1, nsize, nns, qual, etype, pscrn, opt, fapprox, fast)
    
    # Center shift calculation
    vShift = 0.5 if eTimes >= 1 else 0
    
    # Scaling with fmtc.resample as well as correct center shift
    w = last.width
    h = target_height
    sx = 0
    sy = src_top * eScale - vShift
    sw = last.width
    sh = src_height * eScale
    
    if h != last.height or sy != 0 or sh != last.height:
        if h < last.height and invks is True:
            last = core.fmtc.resample(last, w, h, sx, sy, sw, sh, kernel=kernel, taps=taps, a1=a1, a2=a2, invks=True, invkstaps=invkstaps)
        else:
            last = core.fmtc.resample(last, w, h, sx, sy, sw, sh, kernel=kernel, taps=taps, a1=a1, a2=a2)
    
    # Output
    return last


def nnedi3_rpow2_vertical(input, eTimes=1, field=1, nsize=None, nns=None, qual=None, etype=None, pscrn=None, opt=None, fapprox=None, fast=None):
    core = vs.get_core()
    
    if eTimes >= 1:
        last = nnedi3_dh(input, field, nsize, nns, qual, etype, pscrn, opt, fapprox, fast)
        eTimes = eTimes - 1
        field = 0
    else:
        last = input
    
    if eTimes >= 1:
        return nnedi3_rpow2_vertical(last, eTimes, field, nsize, nns, qual, etype, pscrn, opt, fapprox, fast)
    else:
        return last


def nnedi3_dh(input, field=1, nsize=None, nns=None, qual=None, etype=None, pscrn=None, opt=None, fapprox=None, fast=None):
    core = vs.get_core()
    
    sSType = input.format.sample_type
    sbitPS = input.format.bits_per_sample
    if fast is None:
        fast = True
    
    if (pscrn is not None and pscrn > 1) or (fast and sbitPS > 8):
        input8 = mvf.Depth(input, depth=8, sample=vs.INTEGER)
        nn = core.nnedi3.nnedi3(input8, field=field, dh=True, nsize=nsize, nns=nns, qual=qual, etype=etype, pscrn=pscrn, opt=opt, fapprox=fapprox)
        lr = core.fmtc.resample(input, scaleh=1, scalev=2, kernel="bicubic", a1=0, a2=0.5, center=False)
        return mvf.LimitFilter(mvf.Depth(lr, depth=sbitPS, sample=sSType), mvf.Depth(nn, depth=sbitPS, sample=sSType), thr=1.0, elast=2.0)
    else:
        return core.nnedi3.nnedi3(input, field=field, dh=True, nsize=nsize, nns=nns, qual=qual, etype=etype, pscrn=pscrn, opt=opt, fapprox=fapprox)
