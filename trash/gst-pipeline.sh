function convert_WAVPACK_LOSSY () {

    RAW=/tmp/$$.raw

    rm -f -- ${RAW}

    BITS=24
    SAMPLE_RATE=192000

    WV_BITRATE=500 #$[((${BITS}*${SAMPLE_RATE}*280)/(16*44100))]
    WV_X=1

	#
    GST=()

    # INPUT FILE
    GST+=( filesrc name=src location=${1} )
    
    # DECODE
    GST+=( ! decodebin name=decoder )
    
    # RATE
    GST+=( ! audiorate )

    # CONVERT
    if false ; then
        GST+=( ! audioconvert )
    fi

    # FORMAT
    GST+=( ! audio/x-raw,
        rate=${SAMPLE_RATE},
        channels=1,
        format=S${BITS}LE
    )

    # RESAMPLE
    if false ; then
        GST+=( ! audioresample
              quality=10
            # resample-method=GST_AUDIO_RESAMPLER_METHOD_NEAREST
              resample-method=GST_AUDIO_RESAMPLER_METHOD_LINEAR
            # resample-method=GST_AUDIO_RESAMPLER_METHOD_CUBIC
            # resample-method=GST_AUDIO_RESAMPLER_METHOD_BLACKMAN_NUTTALL
            # resample-method=GST_AUDIO_RESAMPLER_METHOD_KAISER
              sinc-filter-auto-threshold=$[4*1024*1024]
              sinc-filter-interpolation=GST_AUDIO_RESAMPLER_FILTER_INTERPOLATION_NONE
            # sinc-filter-interpolation=GST_AUDIO_RESAMPLER_FILTER_INTERPOLATION_LINEAR
            # sinc-filter-interpolation=GST_AUDIO_RESAMPLER_FILTER_INTERPOLATION_CUBIC
            # sinc-filter-mode=GST_AUDIO_RESAMPLER_FILTER_MODE_INTERPOLATED
              sinc-filter-mode=GST_AUDIO_RESAMPLER_FILTER_MODE_FULL
            # sinc-filter-mode=GST_AUDIO_RESAMPLER_FILTER_MODE_AUTO
        )
    fi

    # CONVERT
    if false ; then
        GST+=( ! audioconvert
              dithering=GST_AUDIO_DITHER_NONE
            # dithering=GST_AUDIO_DITHER_RPDF
            # dithering=GST_AUDIO_DITHER_TPDF
            # dithering=GST_AUDIO_DITHER_TPDF_HF
            # dithering-threshold=20
              noise-shaping=GST_AUDIO_NOISE_SHAPING_NONE
            # noise-shaping=GST_AUDIO_NOISE_SHAPING_ERROR_FEEDBACK
            # noise-shaping=GST_AUDIO_NOISE_SHAPING_SIMPLE
            # noise-shaping=GST_AUDIO_NOISE_SHAPING_MEDIUM
            # noise-shaping=GST_AUDIO_NOISE_SHAPING_HIGH
        )
    fi

    # OUTPUT FILE
    GST+=( ! filesink location=${RAW} )

    # TODO: FIXME: VAI PRESERVAR AS TAGS YOUTUBE/URL?
    if gst-launch-1.0 --quiet ${GST[@]} ; then
        if wavpack -hh -b${WV_BITRATE} -x${WV_X} -c ${RAW} --raw-pcm=${SAMPLE_RATE},${BITS}s,1,le -o ${2}.wv ; then
            return 0
        fi
    fi

    return 1
}
