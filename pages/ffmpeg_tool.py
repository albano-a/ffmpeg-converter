import streamlit as st
import ffmpeg
import os
import uuid
import os
from utils import convert_file

st.title("FFmpeg Media Converter")

uploaded_file = st.file_uploader(
    "Upload media file", type=["mp4", "mp3", "mov", "avi", "mkv", "wav", "flac", "ogg"]
)

if uploaded_file:
    up = (
        st.video(uploaded_file)
        if uploaded_file.type.startswith("video")
        else st.audio(uploaded_file)
    )

    st.markdown("### Conversion Options")
    out_format = st.selectbox(
        "Output format", ["mp4", "mp3", "wav", "avi", "mov", "mkv", "flac", "ogg"]
    )
    start = st.text_input("Start time (e.g. 00:00:10)", value="")
    duration = st.text_input("Duration (e.g. 00:00:30)", value="")

    if st.button("Convert"):
        with st.spinner("Converting file..."):
            input_path = (
                f"ffmpeg/input_{uuid.uuid4()}.{uploaded_file.name.split('.')[-1]}"
            )
            output_path = f"ffmpeg/output_{uuid.uuid4()}.{out_format}"
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                if uploaded_file.type.startswith("audio") and out_format in [
                    "mp4",
                    "mkv",
                    "mov",
                    "avi",
                ]:
                    input_color = ffmpeg.input(
                        "color=size=1280x720:rate=30:color=black", f="lavfi", t=30
                    )
                    input_audio = ffmpeg.input("audio.mp3")
                    (
                        ffmpeg.concat(input_color, input_audio, v=1, a=1)
                        .output("output.mp4")
                        .run(overwrite_output=True)
                    )
                else:
                    convert_file(
                        input_path, output_path, start=start, duration=duration
                    )
                st.success("Conversion complete.")
                with open(output_path, "rb") as f:
                    st.download_button(
                        "Download Converted File",
                        f,
                        file_name=os.path.basename(output_path),
                    )
            except Exception as e:
                st.error(f"Error: {e}")
