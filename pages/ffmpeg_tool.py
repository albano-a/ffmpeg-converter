import streamlit as st
import ffmpeg
import os
import uuid
import os
from utils import convert_file
import tempfile  # Import tempfile

st.title("FFmpeg Media Converter")

uploaded_file = st.file_uploader(
    "Upload media file", type=["mp4", "mp3", "mov", "avi", "mkv", "wav", "flac", "ogg"]
)

if uploaded_file:
    file_type = uploaded_file.type
    if file_type.startswith("video"):
        st.video(uploaded_file)
    elif file_type.startswith("audio"):
        st.audio(uploaded_file)

    uploaded_file.seek(0)

    st.markdown("### Conversion Options")
    out_format = st.selectbox(
        "Output format", ["mp4", "mp3", "wav", "avi", "mov", "mkv", "flac", "ogg"]
    )
    start_str = st.text_input("Start time (e.g. 00:00:10 or 10 for seconds)", value="")
    duration_str = st.text_input("Duration (e.g. 00:00:30 or 30 for seconds)", value="")

    if st.button("Convert"):
        with st.spinner("Converting file..."):
            input_bytes = uploaded_file.getvalue()  # Read all bytes into memory
            input_file_extension = uploaded_file.name.split(".")[-1]

            # try:
            output_cli_options = {}
            if start_str:
                output_cli_options["ss"] = start_str
            if duration_str:
                output_cli_options["t"] = duration_str

            download_filename = f"converted_output.{out_format}"
            output_mime_type = f"{'video' if out_format in ['mp4', 'mkv', 'mov', 'avi'] else 'audio'}/{out_format}"

            if file_type.startswith("audio") and out_format in [
                "mp4",
                "mkv",
                "mov",
                "avi",
            ]:
                # Audio to Video (with black screen)
                # Use a temporary file for the audio input to simplify ffmpeg-python stream management
                temp_audio_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=f".{input_file_extension}"
                    ) as tmp_audio_file:
                        tmp_audio_file.write(input_bytes)
                        temp_audio_path = tmp_audio_file.name

                    # Black screen video input, make it long, actual duration determined by audio or output -t
                    input_color = ffmpeg.input(
                        "color=size=1280x720:rate=25:color=black",
                        format="lavfi",
                        t="01:00:00",  # 1 hour, effectively "infinite" for most clips
                    )
                    input_audio_stream = ffmpeg.input(temp_audio_path)

                    current_cli_options = output_cli_options.copy()
                    current_cli_options["vcodec"] = "libx264"
                    current_cli_options["acodec"] = "aac"
                    # Default behavior: output is as long as the longest stream.
                    # If user specifies output duration 't', it takes precedence.

                    process = ffmpeg.output(
                        input_color["v"],
                        input_audio_stream["a"],
                        "pipe:1",
                        format=out_format,
                        **current_cli_options,
                    ).run_async(pipe_stdout=True, pipe_stderr=True)
                    out_bytes, err_bytes = process.communicate()

                finally:
                    if temp_audio_path and os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)  # Clean up the temporary file

            else:
                # General conversion (video-video, video-audio, audio-audio)
                general_cli_options = output_cli_options.copy()
                if out_format == "mp4":  # Example: add movflags for mp4
                    general_cli_options["movflags"] = "+faststart"

                # Input stream from pipe, specify input format
                stream_input = ffmpeg.input("pipe:0", format=input_file_extension)

                # Determine output streams
                if file_type.startswith("video") and out_format in [
                    "mp3",
                    "wav",
                    "flac",
                    "ogg",
                ]:  # Video to Audio
                    output_stream_args = [stream_input.audio]
                else:  # Video to Video or Audio to Audio
                    output_stream_args = [
                        stream_input
                    ]  # Let ffmpeg decide streams (video and/or audio)

                process = ffmpeg.output(
                    *output_stream_args,
                    "pipe:1",
                    format=out_format,
                    **general_cli_options,
                ).run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
                out_bytes, err_bytes = process.communicate(input=input_bytes)

            # Check process result
            if process.returncode != 0:
                st.error(f"FFmpeg Error: {err_bytes.decode('utf8', errors='ignore')}")
            else:
                st.success("Conversion complete.")
                st.download_button(
                    "Download Converted File",
                    data=out_bytes,
                    file_name=download_filename,
                    mime=output_mime_type,
                )

            # except ffmpeg.Error as e:
            #     st.error(
            #         f"ffmpeg-python error: {e.stderr.decode('utf8', errors='ignore') if e.stderr else str(e)}"
            #     )
            # except Exception as e:
            #     st.error(f"An unexpected error occurred: {str(e)}")
