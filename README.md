# Jaehyun Next Door

An unofficial, fan-made Codex pet inspired by BOYNEXTDOOR Myung Jaehyun, pairing a realistic face with a chibi body. Wearing a soft sailor outfit and carrying a little microphone, Jaehyun Next Door keeps you company with gentle waves, small hops, curious tilts and sixteen look directions.

## Get the pet

Find Jaehyun Next Door on either pet-sharing site:

- [codex-pets.net](https://codex-pets.net/#/pets/jaehyun-next-door)
- [codex-pet.org](https://codex-pet.org/pets/jaehyun-next-door)

## Use a cloud pet

1. Download the raw [`spritesheet.webp`](spritesheet.webp). In ChatGPT’s **Settings → Personalization → Pet**, choose **Upload pet**, or ask the Pets plugin to upload it as **Jaehyun Next Door**. If it is already in your cloud pet library, skip this step.
2. Select **Jaehyun Next Door** in the pet picker. In the desktop app, open **Settings → Pets** (or **Mini & Pets**, depending on the version).

No local `pets` folder or `pet.json` is needed for a cloud pet. To update it, replace the sprite sheet on the existing cloud pet through the pet editor or Pets plugin.

The [official guide](https://learn.chatgpt.com/docs/pets) documents uploads and says local pets do not automatically sync to the web. Our desktop checks found separate local and cloud copies; replacing local files left the cloud copy unchanged.

## Local installation (alternative)

1. Clone this repository, or download the raw [`pet.json`](pet.json) and [`spritesheet.webp`](spritesheet.webp) files.
2. Create a `jaehyun-next-door` folder inside your Codex home directory’s `pets` folder. By default, this is `~/.codex/pets/jaehyun-next-door/` on macOS and `%USERPROFILE%\.codex\pets\jaehyun-next-door\` on Windows. If you use a custom `CODEX_HOME`, use its `pets` folder instead.
3. Copy both files into that folder:

   ```text
   pets/
   └── jaehyun-next-door/
       ├── pet.json
       └── spritesheet.webp
   ```

4. Open **Settings → Mini & Pets**, click the refresh/reload button, then select **Jaehyun Next Door**.

Only these two files are needed for local installation. To update a local pet, replace both files and refresh the pet picker again.

## Animation examples

View the gallery online: [Jaehyun Next Door · Animation examples](https://codex-pets.isarvin.com/jaehyun-next-door/).

To view it offline, clone this repository and open [`examples/index.html`](examples/index.html) in your browser. The gallery includes:

- **Nine animations:** resting, moving right, moving left, hello wave, little hop, sheepish reaction, curious head tilt, mic rehearsal and thoughtful check.
- **Frame-by-frame previews:** a separate GIF and a numbered frame sheet for each animation.
- **Sixteen look directions:** an individual direction selector and a clockwise preview.
- **Playback controls:** pause and play, with reduced-motion preferences respected.
- **Automatic light and dark themes:** follows your system preference. Animation previews retain their original light backgrounds.

Standard animation previews use Codex’s frame timings. The look-around preview is an illustrative sweep; in Codex, gaze is controlled by the app. The gallery plays without audio and requires no external resources.

## Social media examples

Watch the [demonstration video](examples/social-media/demo.mp4) or download the [cover image](examples/social-media/cover.png). The 45-second video shows the pet in use on the desktop, followed by its animations in a desktop-radio layout, with Chinese captions and a licensed piano soundtrack.

See [social media examples](examples/social-media/README.md) for details and instructions on rebuilding the video.
