#!/usr/bin/env python

import argparse, os, json

parser = argparse.ArgumentParser(description='Process a neural style job directory')
parser.add_argument('directory', type=str,
                    help='Directory containing the job information, content and styles')
parser.add_argument('--shutdown', action='store_true',
                    default=False,
                    help='Shutdown on completion')
parser.add_argument('--test', action='store_true',
                    default=False,
                    help='Do not execute commands')
parser.add_argument('--size', type=int,
					default=None,
                    help='Override target size of output images in job')
parser.add_argument('--overwrite', action='store_true',
                    default=False,
                    help='Overwrite existing outputs')


args = parser.parse_args()


def run(cmd, force=False):
	print(cmd)

	if args.test and not force:
		return 0

	return os.system(cmd)


if not os.path.exists(args.directory):
	print("Directory does not exist")
	exit(1)

job_file = os.path.join(args.directory, "job.json")
if not os.path.exists(job_file):
	print("job.json not in directory")
	exit(1)

with open(job_file, 'r') as f:
    job = json.loads(f.read())

print("Read configuration: ")
print(json.dumps(job, sort_keys=True, indent=4, separators=(',', ': ')))

out_dir = os.path.join(args.directory, "output")
if os.path.exists(out_dir):
	if not args.overwrite:
		print("ERROR: Output directory exists (and no --overwrite): {}".format(out_dir))
		exit(1)
	else:
		print("Output directory exists: {}".format(out_dir))
else:
	os.makedirs(out_dir)
	print("Created directory: {}".format(out_dir))

for artwork in job['artworks']:
	contents, styles = artwork['contents'], artwork['styles']
	art_args = artwork['args'] if 'args' in artwork else []
	
	if args.size and 'image_size' in art_args:
		print("Override image_size to {}".format(args.size))
		art_args['image_size'] = args.size

	for content in contents:
		for style in styles:
			print("Transferring {} style to {} content".format(style, content))
			out_filename = "{}+{}.png".format(style, content)

			out_path = os.path.abspath(os.path.join(out_dir, out_filename))
			style_path = os.path.abspath(os.path.join(args.directory, "styles", style + ".jpg"))
			content_path = os.path.abspath(os.path.join(args.directory, "contents", content + ".jpg"))

			ns_args = ['-{} {}'.format(k, art_args[k]) for k in art_args]

			if run("lua neural_style.lua -style_image {} -content_image {} -backend cudnn {} -output_image {}".format(
					style_path, content_path, ' '.join(ns_args), out_path
				)) != 0:
				print("ERROR: lua error")
				exit(1)

			# TODO:
			# make archive
			# upload to server
			# cleanup
			# shutdown if necessary