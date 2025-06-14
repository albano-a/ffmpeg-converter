import ffmpeg


def convert_file(input_path, output_path, start="", duration=""):
    stream = ffmpeg.input(input_path)

    if start:
        stream = ffmpeg.input(input_path, ss=start)

    if duration:
        stream = ffmpeg.output(stream, output_path, t=duration)
    else:
        stream = ffmpeg.output(stream, output_path)

    ffmpeg.run(stream, overwrite_output=True)
