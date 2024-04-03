./repos/linux_scripts/build_kaleido x64
source venv/bin/activate
sudo chmod a+rwx . -R

cd ./repos/kaleido/py
pip install .

cd ../../../
cp ./repos/build/kaleido venv/lib/python3.10/site-packages/kaleido -r
rm venv/lib/python3.10/site-packages/kaleido/executable -r
mv venv/lib/python3.10/site-packages/kaleido/kaleido venv/lib/python3.10/site-packages/kaleido/executable 