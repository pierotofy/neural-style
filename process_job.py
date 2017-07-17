#!/usr/bin/env python

import argparse, os, json, glob, math
import requests
import shutil

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
parser.add_argument('--upload-to',
                    default=None,
                    help='URL of the http end-point where the results should be uploaded to')


args = parser.parse_args()


def run(cmd, force=False):
    print(cmd)

    if args.test and not force:
        return 0

    return os.system(cmd)

try:
    directory = args.directory

    if directory.endswith(".tar.gz"):
        job_name = os.path.basename(directory).replace('.tar.gz', '')
        print("Job: " + job_name)
        print("Downloading: " + directory)
        run("rm *.tar.gz")

        r = requests.get(directory, stream=True)
        if r.status_code == 200:
            with open(os.path.basename(directory), 'wb') as f:
                for chunk in r:
                    f.write(chunk)

        run("tar -xvf {}.tar.gz".format(job_name))
        run("rm *.tar.gz")
        directory = job_name

    if not os.path.exists(directory):
        raise RuntimeError("Directory does not exist")

    job_file = os.path.join(directory, "job.json")
    if not os.path.exists(job_file):
        raise RuntimeError("job.json not in directory")

    with open(job_file, 'r') as f:
        job = json.loads(f.read())

    print("Read configuration: ")
    print(json.dumps(job, sort_keys=True, indent=4, separators=(',', ': ')))

    out_dir = os.path.join(directory, "output")
    if os.path.exists(out_dir):
        if not args.overwrite:
            raise RuntimeError("ERROR: Output directory exists (and no --overwrite): {}".format(out_dir))
        else:
            print("Output directory exists: {}".format(out_dir))
    else:
        os.makedirs(out_dir)
        print("Created directory: {}".format(out_dir))

    for artwork in job['artworks']:
        contents, styles = artwork['contents'], artwork['styles']
        art_args = artwork['args'] if 'args' in artwork else {}

        if isinstance(contents, str) or isinstance(contents, unicode):
            if contents == '*':
                contents = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(directory, "contents", "*.jpg"))]
                print("Found wildcard contents: " + str(contents))
            else:
                raise RuntimeError("Invalid contents value: " + contents)

        if isinstance(styles, str) or isinstance(styles, unicode):
            if styles == '*':
                styles = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(directory, "styles", "*.jpg"))]
                print("Found wildcard styles: " + str(styles))
            else:
                raise RuntimeError("Invalid contents value: " + styles)
    
        
        if args.size:
            print("Override image_size to {}".format(args.size))
            art_args['image_size'] = args.size
        else:
            art_args['image_size'] = 512


        for content in contents:
            for style in styles:
                print("Transferring {} style to {} content".format(style, content))
                out_filename = "{}+{}+{}.png".format(style, content, '-'.join(['{}_{}'.format(k, art_args[k]) for k in art_args]))

                out_path = os.path.abspath(os.path.join(out_dir, out_filename))
                style_path = os.path.abspath(os.path.join(directory, "styles", style + ".jpg"))
                content_path = os.path.abspath(os.path.join(directory, "contents", content + ".jpg"))

                extra_args = {}
                extra_args['num_iterations'] = 1000
                extra_args['backend'] = 'cudnn'
                extra_args['optimizer'] = 'adam'
                extra_args['tv_weight'] = 0

                current_resolution = 512

                while art_args['image_size'] > current_resolution:
                    print("Generating intermediate {}px image".format(current_resolution))

                    intermediate_out_filename = "{}+{}+{}+inter-{}.png".format(style, content, '-'.join(['{}_{}'.format(k, art_args[k]) for k in art_args]), current_resolution)
                    intermediate_out_path = os.path.abspath(os.path.join(out_dir, intermediate_out_filename))

                    if not os.path.exists(intermediate_out_path):
                        if run("qlua neural_style.lua -save_iter 0 -style_image {} -content_image {} {} {} -output_image {} -image_size {}".format(
                            style_path, content_path, ' '.join(['-{} {}'.format(k, extra_args[k]) for k in extra_args]), ' '.join(['-{} {}'.format(k, art_args[k]) for k in art_args]), intermediate_out_path, current_resolution
                        )) != 0:
                            raise RuntimeError("ERROR: lua error")
                    else:
                        print("Intermediate image {}px already exists".format(current_resolution))

                    current_resolution *= 2
                    extra_args['num_iterations'] = math.floor(extra_args['num_iterations'] / 2)

                    extra_args['init'] = 'image'
                    extra_args['init_image'] = intermediate_out_path

                if run("qlua neural_style.lua -style_image {} -content_image {} {} {} -output_image {}".format(
                        style_path, content_path, ' '.join(['-{} {}'.format(k, extra_args[k]) for k in extra_args]), ' '.join(['-{} {}'.format(k, art_args[k]) for k in art_args]), out_path
                    )) != 0:
                    raise RuntimeError("ERROR: lua error")


    if args.upload_to:
        job_name = os.path.basename(directory)
        print("Archiving...")
        archive_filename = "{}-output.tar.gz".format(job_name)
        run("tar -cvzf {} {}".format(archive_filename, out_dir), True)

        print("Uploading to {}".format(args.upload_to))

        files = [('files', (os.path.basename(archive_filename), open(archive_filename, 'rb'), 'application/tar+gzip'))]
        res = requests.post(args.upload_to, files=files)
        print(res.content)
        if res.status_code == 200 and "success" in str(res.content):
            # Cleanup
            run("rm {}".format(archive_filename))
            run("rm -r {}".format(directory))
        else:
            print("ERROR: Could not upload file to server!")

    if args.shutdown:
        run("sudo shutdown -h now")

except RuntimeError as e:
    print("ERROR: " + str(e))
    exit(1)