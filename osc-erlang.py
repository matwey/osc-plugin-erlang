from osc import core, cmdln
import tempfile
import rpm
import requests
import re


re_refs_tags = re.compile(r'refs/tags/(.*)')
re_OTP = re.compile(r'OTP-(.*)')


def get_github_tags(self, prefix, owner="erlang", repo="otp"):
	url = "https://api.github.com/repos/{}/{}/git/matching-refs/tags/{}".format(owner, repo, prefix)
	req = requests.get(url)
	req.raise_for_status()
	return [re_refs_tags.match(x['ref']).groups(1)[0] for x in req.json()]

def get_github_version(self, major):
	prefix = "OTP-{}".format(major)
	return re_OTP.match(self.get_github_tags(prefix)[-1]).groups(1)[0]

def get_obs_version(self, project, package="erlang", filename=None):
	if filename is None:
		filename = "{}.spec".format(package)

	with tempfile.NamedTemporaryFile() as temp_file:
		target_filename = temp_file.name

		core.get_source_file(conf.config['apiurl'], project, package, filename, target_filename)
		s = rpm.spec(target_filename)
		obs_version = s.sourceHeader[rpm.RPMTAG_VERSION].decode("ascii")

		major, *_ = obs_version.split(".")

		return obs_version, major

def format_table(self, table):
	w = [max([len(x) for x in col]) for col in zip(*table)]
	fmt = "\t".join(['{{{0}:<{1}}}'.format(*x) for x in enumerate(w)])
	return "\n".join([fmt.format(*row) for row in table])

@cmdln.alias('erl')
@cmdln.option('-p', "--project",
	help="erlang package project (default devel:languages:erlang:Factory)",
	default="devel:languages:erlang:Factory")
def do_erlang(self, subcmd, opts):
	"""${cmd_name} helper tools to keep OTP/Erlang packages up to date

	${cmd_usage}
	${cmd_option_list}
	"""

	project = opts.project

	obs_version, major = self.get_obs_version(project)
	github_version = self.get_github_version(major)

	table = [
		["project", "package", "upstream", "up to date"],
		[project, obs_version, github_version, "yes" if obs_version == github_version else "no"],]
	print(self.format_table(table))
