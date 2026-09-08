import asyncio

from backend.services.avatar.local_provider import LocalLinlyTalkerProvider


async def main():
    provider = LocalLinlyTalkerProvider()

    result = await provider.generate_video(
        audio_url="/media/f5bf1327-323e-4c70-b88f-a8530ae6175d.wav",
        script_text="Hello. This is a test of the local AI Teacher avatar.",
    )

    print("STATUS:", result.status)
    print("VIDEO_URL:", result.video_url)
    print("JOB_ID:", result.provider_job_id)


if __name__ == "__main__":
    asyncio.run(main())