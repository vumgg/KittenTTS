import argparse

import soundfile as sf

from kittentts import KittenTTS


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Run KittenTTS and save speech to a WAV file")
	parser.add_argument(
		"--model",
		default="KittenML/kitten-tts-nano-0.8-fp32",
		help="Hugging Face model repo id",
	)
	parser.add_argument(
		"--text",
		default="This is a running example for KittenTTS.",
		help="Text to synthesize",
	)
	parser.add_argument(
		"--voice",
		default="expr-voice-2-f",
		help="Voice id (see --list-voices)",
	)
	parser.add_argument(
		"--speed",
		type=float,
		default=1.0,
		help="Speech speed multiplier",
	)
	parser.add_argument(
		"--output",
		default="output.wav",
		help="Output WAV file path",
	)
	parser.add_argument(
		"--sample-rate",
		type=int,
		default=24000,
		help="Output sample rate",
	)
	parser.add_argument(
		"--list-voices",
		action="store_true",
		help="Print available voices and exit",
	)
	return parser


def main() -> None:
	args = build_parser().parse_args()

	model = KittenTTS(args.model)

	if args.list_voices:
		print("Available voices:")
		for voice_name in model.available_voices:
			print(f"- {voice_name}")
		return

	audio = model.generate(args.text, voice=args.voice, speed=args.speed)
	sf.write(args.output, audio, args.sample_rate)
	print(f"Saved speech to {args.output}")


if __name__ == "__main__":
	main()
