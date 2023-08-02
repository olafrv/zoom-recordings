# Zoom Recordings Downloader

First:

* https://marketplace.zoom.us/user/build (Developer > Build Apps > Server-to-Server OAuth)
* Create a new App with the following scopes: users:admin:read,
* Take note of the ACCOUNT_ID, CLIENT_ID, CLIENT_SECRET
* Be aware of API throttling: 

Easy peasy:
```bash
export ZOOM_ACCOUNT_ID="******"
export ZOOM_CLIENT_ID="******"
export ZOOM_CLIENT_SECRET="******"
export ZOOM_RECORDING_YEAR=2023
export ZOOM_RECORDING_MONTH_FROM=1
export ZOOM_RECORDING_MONTH_TO=8
export ZOOM_USERS_FILTER="olaf.reitmaier@example.com"  # or leave it empty "" but set
pip3 install -r requirements.ext
python3 main.py
``

# References

* Zoom Server to Server OAuth: https://developers.zoom.us/docs/internal-apps/s2s-oauth/
* Inspiration: https://github.com/ricardorodrigues-ca/zoom-recording-downloader