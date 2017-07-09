#!/usr/bin/env python

import argparse, os

parser = argparse.ArgumentParser(description='Process a neural style job from a URL')
parser.add_argument('JOB_URL', type=str,
                    help='Full URL to the neural tyle job file (.tar.gz)')
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

if not args.JOB_URL.endswith(".tar.gz"):
	print("Invalid JOB_URL (must end in .tar.gz")
	exit(1)

job_name = os.path.basename(args.JOB_URL).replace('.tar.gz', '')
print("Job: " + job_name)

def run(cmd, force=False):
	print(cmd)

	if args.test and not force:
		return 0

	return os.system(cmd)


print("Downloading: " + args.JOB_URL)
run("rm *.tar.gz")
run("wget " + args.JOB_URL)
run("tar -xvf {}.tar.gz".format(job_name))

params = []
if args.test: params.append("--test")
if args.shutdown: params.append("--shutdown")
if args.size: params.append("--size " + str(args.size))
if args.overwrite: params.append("--overwrite")

run("python process_job.py {} {}".format(' '.join(params), job_name), True)