cd $HOME/workspace/pyamihtml # or whatever your top dir
rm -rf dist
python setup.py sdist
twine upload dist/* # <login is pypi, not github> I am petermr
# install
pip uninstall pyamihtmlx
#
pip install pyamihtmlx # or whatever version
# pip install --pre pyamihtml==0.0.3a1

