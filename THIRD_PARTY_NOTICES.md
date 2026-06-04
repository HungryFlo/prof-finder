# Third-Party Notices

Prof-Finder is licensed under the [MIT License](LICENSE).

This document lists third-party software **included in or used to build** Prof-Finder
(portable/desktop distribution and source installs). It does not replace the license
text of each component; see the URL or project repository for full terms.

| Section | Scope |
|---------|--------|
| [Python runtime](#python-runtime-dependencies) | Backend and packaged executable (Poetry **main** dependencies and their transitive packages) |
| [Frontend](#frontend-dependencies) | Web UI bundled in releases (`npm` production dependency tree) |
| [Embedding model](#embedding-model-runtime-download) | Downloaded at runtime on first match (not shipped in the git repo) |
| [External services](#external-services-and-data) | APIs and public data sources you connect to at runtime |

**Regenerate this file** (from repo root, with `prof-finder` conda env and `poetry install --with dev`):

```bash
python scripts/generate_third_party_notices.py
```

---

## Python runtime dependencies

The following **156** Python packages are included in production installs (Poetry `main` group, including transitive dependencies).

| Name | Version | License | Author | URL |
|------|---------|---------|--------|-----|
| aiofiles | 25.1.0 | Apache Software License | Tin Tvrtkovic <tinchester@gmail.com> | https://github.com/Tinche/aiofiles |
| aiohappyeyeballs | 2.6.2 | Python Software Foundation License | J. Nick Koston | https://github.com/aio-libs/aiohappyeyeballs |
| aiohttp | 3.13.5 | Apache-2.0 AND MIT | UNKNOWN | https://github.com/aio-libs/aiohttp |
| aiosignal | 1.4.0 | Apache Software License | UNKNOWN | https://github.com/aio-libs/aiosignal |
| aiosqlite | 0.22.1 | MIT License | Amethyst Reese <amethyst@n7.gg> | https://aiosqlite.omnilib.dev |
| alabaster | 0.7.16 | BSD License | Jeff Forcier <jeff@bitprophet.org> | https://alabaster.readthedocs.io/ |
| alphashape | 1.3.1 | MIT License | Kenneth E. Bellock | https://github.com/bellockk/alphashape |
| annotated-doc | 0.0.4 | MIT | =?utf-8?q?Sebasti=C3=A1n_Ram=C3=ADrez?= <tiangolo@gmail.com> | https://github.com/fastapi/annotated-doc |
| annotated-types | 0.7.0 | MIT License | Adrian Garcia Badaracco <1755071+adriangb@users.noreply.github.com>, Samuel Colvin <s@muelcolvin.com>, Zac Hatfield-Dodds <zac@zhd.dev> | https://github.com/annotated-types/annotated-types |
| anyio | 4.12.1 | MIT | Alex Grönholm <alex.gronholm@nextday.fi> | https://anyio.readthedocs.io/en/stable/versionhistory.html |
| arrow | 1.4.0 | Apache Software License | Chris Smith <crsmithdev@gmail.com> | https://github.com/arrow-py/arrow |
| attrs | 25.4.0 | MIT | Hynek Schlawack <hs@ox.cx> | https://www.attrs.org/en/stable/changelog.html |
| babel | 2.17.0 | BSD License | Armin Ronacher | https://babel.pocoo.org/ |
| bcrypt | 5.0.0 | Apache Software License | The Python Cryptographic Authority developers <cryptography-dev@python.org> | https://github.com/pyca/bcrypt/ |
| beautifulsoup4 | 4.14.3 | MIT License | Leonard Richardson <leonardr@segfault.org> | https://www.crummy.com/software/BeautifulSoup/bs4/ |
| bibtexparser | 1.4.3 | LGPLv3 or BSD | Francois Boulogne and other contributors | https://github.com/sciunto-org/python-bibtexparser |
| brotli | 1.2.0 | MIT | The Brotli Authors | https://github.com/google/brotli |
| certifi | 2026.1.4 | Mozilla Public License 2.0 (MPL 2.0) | Kenneth Reitz | https://github.com/certifi/python-certifi |
| cffi | 2.0.0 | MIT | Armin Rigo, Maciej Fijalkowski | https://cffi.readthedocs.io/en/latest/whatsnew.html |
| chardet | 7.4.3 | 0BSD | Dan Blanchard <dan.blanchard@gmail.com> | https://github.com/chardet/chardet |
| charset-normalizer | 3.4.4 | MIT | "Ahmed R. TAHRI" <tahri.ahmed@proton.me> | https://github.com/jawah/charset_normalizer/blob/master/CHANGELOG.md |
| click | 8.1.8 | BSD License | UNKNOWN | https://github.com/pallets/click/ |
| click-log | 0.4.0 | MIT License | Markus Unterwaditzer | https://github.com/click-contrib/click-log |
| colorama | 0.4.6 | BSD License | Jonathan Hartley <tartley@tartley.com> | https://github.com/tartley/colorama |
| Crawl4AI | 0.7.6 | Apache-2.0 | Unclecode | https://github.com/unclecode/crawl4ai |
| cryptography | 43.0.3 | Apache Software License; BSD License | The cryptography developers <cryptography-dev@python.org> | https://github.com/pyca/cryptography |
| cssselect | 1.4.0 | BSD-3-Clause | Ian Bicking <ianb@colorstudy.com> | https://github.com/scrapy/cssselect |
| Deprecated | 1.3.1 | MIT License | Laurent LAPORTE | https://github.com/laurent-laporte-pro/deprecated |
| distro | 1.9.0 | Apache Software License | Nir Cohen | https://github.com/python-distro/distro |
| docutils | 0.21.2 | BSD License; GNU General Public License (GPL); Public Domain; Python Software Foundation License | David Goodger <goodger@python.org> | https://docutils.sourceforge.io |
| ecdsa | 0.19.1 | MIT | Brian Warner | http://github.com/tlsfuzzer/python-ecdsa |
| fake-http-header | 0.3.5 | MIT | Michael Tatarski | https://github.com/MichaelTatarski/fake-http-header |
| fake-useragent | 2.2.0 | Apache-2.0 | Melroy van den Berg <melroy@melroy.org>, Victor Kovtun <hellysmile@gmail.com> | https://github.com/fake-useragent/fake-useragent |
| fastapi | 0.109.2 | MIT | Sebastián Ramírez <tiangolo@gmail.com> | https://github.com/tiangolo/fastapi |
| fastuuid | 0.14.0 | BSD License | UNKNOWN | https://github.com/thedrow/fastuuid/ |
| filelock | 3.24.3 | MIT | UNKNOWN | https://github.com/tox-dev/py-filelock |
| free_proxy | 1.1.3 | MIT License | jundymek | https://github.com/jundymek/free-proxy |
| frozenlist | 1.8.0 | Apache-2.0 | UNKNOWN | https://github.com/aio-libs/frozenlist |
| fsspec | 2026.2.0 | BSD-3-Clause | UNKNOWN | https://github.com/fsspec/filesystem_spec |
| greenlet | 3.2.4 | MIT AND Python-2.0 | Alexey Borzenkov | https://greenlet.readthedocs.io/ |
| h11 | 0.16.0 | MIT License | Nathaniel J. Smith | https://github.com/python-hyper/h11 |
| h2 | 4.3.0 | MIT License | Cory Benfield <cory@lukasa.co.uk> | https://github.com/python-hyper/h2/ |
| hf-xet | 1.3.2 | Apache-2.0 | UNKNOWN | https://github.com/huggingface/xet-core |
| hpack | 4.1.0 | MIT License | Cory Benfield <cory@lukasa.co.uk> | https://github.com/python-hyper/hpack/ |
| httpcore | 1.0.9 | BSD-3-Clause | Tom Christie <tom@tomchristie.com> | https://www.encode.io/httpcore/ |
| httptools | 0.7.1 | MIT | Yury Selivanov <yury@magic.io> | https://github.com/MagicStack/httptools |
| httpx | 0.28.1 | BSD License | Tom Christie <tom@tomchristie.com> | https://github.com/encode/httpx |
| huey | 3.0.0 | MIT License (see https://github.com/coleifer/huey) | Charles Leifer <coleifer@gmail.com> | https://github.com/coleifer/huey |
| huggingface_hub | 1.5.0 | Apache Software License | Hugging Face, Inc. | https://github.com/huggingface/huggingface_hub |
| humanize | 4.15.0 | MIT | Jason Moiron <jmoiron@jmoiron.net> | https://github.com/python-humanize/humanize |
| hyperframe | 6.1.0 | MIT License | Cory Benfield <cory@lukasa.co.uk> | https://github.com/python-hyper/hyperframe/ |
| idna | 3.11 | BSD-3-Clause | Kim Davies <kim+pypi@gumleaf.org> | https://github.com/kjd/idna |
| imagesize | 1.4.1 | MIT License | Yoshiki Shibukawa | https://github.com/shibukawa/imagesize_py |
| importlib_metadata | 9.0.0 | Apache-2.0 | "Jason R. Coombs" <jaraco@jaraco.com> | https://github.com/python/importlib_metadata |
| Jinja2 | 3.1.6 | BSD License | UNKNOWN | https://github.com/pallets/jinja/ |
| jiter | 0.12.0 | MIT License | Samuel Colvin <s@muelcolvin.com> | https://github.com/pydantic/jiter/ |
| joblib | 1.5.3 | BSD-3-Clause | Gael Varoquaux <gael.varoquaux@normalesup.org> | https://joblib.readthedocs.io |
| jsonschema | 4.26.0 | MIT | Julian Berman <Julian+jsonschema@GrayVines.com> | https://github.com/python-jsonschema/jsonschema |
| jsonschema-specifications | 2025.9.1 | MIT | Julian Berman <Julian+jsonschema-specifications@GrayVines.com> | https://github.com/python-jsonschema/jsonschema-specifications |
| lark | 1.3.1 | MIT License | Erez Shinan <erezshin@gmail.com> | https://github.com/lark-parser/lark |
| litellm | 1.80.0 | MIT License | BerriAI | https://litellm.ai |
| lxml | 5.4.0 | BSD License | lxml dev team | https://lxml.de/ |
| markdown-it-py | 3.0.0 | MIT License | Chris Sewell <chrisj_sewell@hotmail.com> | https://github.com/executablebooks/markdown-it-py |
| MarkupSafe | 3.0.3 | BSD-3-Clause | UNKNOWN | https://github.com/pallets/markupsafe/ |
| mdurl | 0.1.2 | MIT License | Taneli Hukkinen <hukkin@users.noreply.github.com> | https://github.com/executablebooks/mdurl |
| modelscope | 1.37.0 | Apache-2.0 | ModelScope team | https://github.com/modelscope/modelscope |
| mpmath | 1.3.0 | BSD License | Fredrik Johansson | http://mpmath.org/ |
| multidict | 6.7.1 | Apache License 2.0 | Andrew Svetlov | https://github.com/aio-libs/multidict |
| networkx | 3.4.2 | BSD License | Aric Hagberg <hagberg@lanl.gov> | https://networkx.org/ |
| nltk | 3.9.4 | Apache Software License | NLTK Team | https://www.nltk.org/ |
| numpy | 2.2.6 | BSD License | Travis E. Oliphant et al. | https://numpy.org |
| openai | 1.109.1 | Apache Software License | OpenAI <support@openai.com> | https://github.com/openai/openai-python |
| outcome | 1.3.0.post0 | Apache Software License; MIT License | Frazer McLean | https://github.com/python-trio/outcome |
| packaging | 26.0 | Apache-2.0 OR BSD-2-Clause | Donald Stufft <donald@stufft.io> | https://github.com/pypa/packaging |
| passlib | 1.7.4 | BSD | Eli Collins | https://passlib.readthedocs.io |
| patchright | 1.60.0 | Apache-2.0 | Microsoft Corporation, patched by github.com/Kaliiiiiiiiii-Vinyzu/ | https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python |
| pillow | 12.2.0 | MIT-CMU | Jeffrey 'Alex' Clark <aclark@aclark.net> | https://python-pillow.github.io |
| playwright | 1.60.0 | Apache-2.0 | Microsoft Corporation | https://github.com/Microsoft/playwright-python |
| propcache | 0.5.2 | Apache Software License | Andrew Svetlov | https://github.com/aio-libs/propcache |
| psutil | 7.2.2 | BSD-3-Clause | Giampaolo Rodola | https://github.com/giampaolo/psutil |
| pyasn1 | 0.6.2 | BSD-2-Clause | Ilya Etingof <etingof@gmail.com> | https://github.com/pyasn1/pyasn1 |
| pycparser | 2.23 | BSD License | Eli Bendersky | https://github.com/eliben/pycparser |
| pydantic | 2.12.5 | MIT | Samuel Colvin <s@muelcolvin.com>, Eric Jolibois <em.jolibois@gmail.com>, Hasan Ramezani <hasan.r67@gmail.com>, Adrian Garcia Badaracco <1755071+adriangb@users.noreply.github.com>, Terrence Dorsey <terry@pydantic.dev>, David Montague <david@pydantic.dev>, Serge Matveenko <lig@countzero.co>, Marcelo Trylesinski <marcelotryle@gmail.com>, Sydney Runkle <sydneymarierunkle@gmail.com>, David Hewitt <mail@davidhewitt.io>, Alex Hall <alex.mojaki@gmail.com>, Victorien Plot <contact@vctrn.dev>, Douwe Maan <hi@douwe.me> | https://github.com/pydantic/pydantic |
| pydantic_core | 2.41.5 | MIT | Samuel Colvin <s@muelcolvin.com>, Adrian Garcia Badaracco <1755071+adriangb@users.noreply.github.com>, David Montague <david@pydantic.dev>, David Hewitt <mail@davidhewitt.dev>, Sydney Runkle <sydneymarierunkle@gmail.com>, Victorien Plot <contact@vctrn.dev> | https://github.com/pydantic/pydantic-core |
| pyee | 13.0.1 | MIT License | Josh Holbrook <josh.holbrook@gmail.com> | https://github.com/jfhbrook/pyee |
| Pygments | 2.19.2 | BSD License | Georg Brandl <georg@python.org> | https://pygments.org |
| pylatexenc | 2.10 | MIT License | Philippe Faist | https://github.com/phfaist/pylatexenc |
| pyOpenSSL | 25.1.0 | Apache Software License | The pyOpenSSL developers | https://pyopenssl.org/ |
| pyparsing | 3.3.2 | MIT | Paul McGuire <ptmcg.gm+pyparsing@gmail.com> | https://github.com/pyparsing/pyparsing/ |
| pypinyin | 0.53.0 | MIT License | mozillazg, 闲耘 | https://github.com/mozillazg/python-pinyin |
| PySocks | 1.7.1 | BSD | Anorov | https://github.com/Anorov/PySocks |
| python-dateutil | 2.9.0.post0 | Apache Software License; BSD License | Gustavo Niemeyer | https://github.com/dateutil/dateutil |
| python-dotenv | 1.2.1 | BSD-3-Clause | Saurabh Kumar <me+github@saurabh-kumar.com> | https://github.com/theskumar/python-dotenv |
| python-jose | 3.5.0 | MIT License | Michael Davis | http://github.com/mpdavis/python-jose |
| python-multipart | 0.0.6 | Apache-2.0 | Andrew Dunham <andrew@du.nham.ca> | https://github.com/andrew-d/python-multipart |
| PyYAML | 6.0.3 | MIT License | Kirill Simonov | https://pyyaml.org/ |
| rank-bm25 | 0.2.2 | Apache2.0 | D. Brown | https://github.com/dorianbrown/rank_bm25 |
| referencing | 0.37.0 | MIT | Julian Berman <Julian+referencing@GrayVines.com> | https://github.com/python-jsonschema/referencing |
| regex | 2026.2.28 | Apache-2.0 AND CNRI-Python | Matthew Barnett <regex@mrabarnett.plus.com> | https://github.com/mrabarnett/mrab-regex |
| requests | 2.32.5 | Apache Software License | Kenneth Reitz | https://requests.readthedocs.io |
| rich | 13.9.4 | MIT License | Will McGugan | https://github.com/Textualize/rich |
| rpds-py | 0.30.0 | MIT | Julian Berman <Julian+rpds@GrayVines.com> | https://github.com/crate-py/rpds |
| rsa | 4.9.1 | Apache Software License | Sybren A. Stüvel | https://stuvel.eu/rsa |
| rtree | 1.4.1 | MIT | Sean Gillies <sean.gillies@gmail.com> | https://github.com/Toblerity/rtree |
| safetensors | 0.7.0 | Apache Software License | Nicolas Patry <patry.nicolas@protonmail.com> | https://github.com/huggingface/safetensors |
| scholarly | 1.7.11 | Unlicense | Steven A. Cholewiak, Panos Ipeirotis, Victor Silva, Arun Kannawadi | https://github.com/scholarly-python-package/scholarly |
| scikit-learn | 1.7.2 | BSD-3-Clause | UNKNOWN | https://scikit-learn.org |
| scipy | 1.15.3 | BSD License | UNKNOWN | https://scipy.org/ |
| selenium | 4.36.0 | Apache-2.0 | UNKNOWN | https://www.selenium.dev |
| sentence-transformers | 5.2.3 | Apache Software License | Nils Reimers <info@nils-reimers.de>, Tom Aarsen <tom.aarsen@huggingface.co> | https://www.SBERT.net |
| shapely | 2.1.2 | BSD License | Sean Gillies | https://github.com/shapely/shapely |
| shellingham | 1.5.4 | ISC License (ISCL) | Tzu-ping Chung | https://github.com/sarugaku/shellingham |
| six | 1.17.0 | MIT License | Benjamin Peterson | https://github.com/benjaminp/six |
| sniffio | 1.3.1 | Apache Software License; MIT License | "Nathaniel J. Smith" <njs@pobox.com> | https://github.com/python-trio/sniffio |
| snowballstemmer | 2.2.0 | BSD License | Snowball Developers | https://github.com/snowballstem/snowball |
| sortedcontainers | 2.4.0 | Apache Software License | Grant Jenks | http://www.grantjenks.com/docs/sortedcontainers/ |
| soupsieve | 2.8.3 | MIT | Isaac Muse <Isaac.Muse@gmail.com> | https://github.com/facelessuser/soupsieve |
| Sphinx | 7.4.7 | BSD License | Georg Brandl <georg@python.org> | https://www.sphinx-doc.org/ |
| sphinx_rtd_theme | 3.1.0 | MIT License | Dave Snider, Read the Docs, Inc. & contributors | https://sphinx-rtd-theme.readthedocs.io/ |
| sphinxcontrib-applehelp | 2.0.0 | BSD License | Georg Brandl <georg@python.org> | https://www.sphinx-doc.org/ |
| sphinxcontrib-devhelp | 2.0.0 | BSD License | Georg Brandl <georg@python.org> | https://www.sphinx-doc.org/ |
| sphinxcontrib-htmlhelp | 2.1.0 | BSD License | Georg Brandl <georg@python.org> | https://www.sphinx-doc.org/ |
| sphinxcontrib-jquery | 4.1 | BSD License | Adam Turner | https://github.com/sphinx-contrib/jquery/ |
| sphinxcontrib-jsmath | 1.0.1 | BSD License | Georg Brandl | http://sphinx-doc.org/ |
| sphinxcontrib-qthelp | 2.0.0 | BSD License | Georg Brandl <georg@python.org> | https://www.sphinx-doc.org/ |
| sphinxcontrib-serializinghtml | 2.0.0 | BSD License | Georg Brandl <georg@python.org> | https://www.sphinx-doc.org/ |
| SQLAlchemy | 2.0.46 | MIT | Mike Bayer | https://www.sqlalchemy.org |
| sse-starlette | 2.4.1 | BSD-3-Clause | sysid <sysid@gmx.de> | https://github.com/sysid/sse-starlette |
| starlette | 0.36.3 | BSD-3-Clause | Tom Christie <tom@tomchristie.com> | https://github.com/encode/starlette |
| sympy | 1.14.0 | BSD License | SymPy development team | https://sympy.org |
| tf-playwright-stealth | 1.2.0 | MIT License | UNKNOWN | https://www.agentql.com/ |
| threadpoolctl | 3.6.0 | BSD License | Thomas Moreau | https://github.com/joblib/threadpoolctl |
| tiktoken | 0.13.0 | MIT License  Copyright (c) 2022 OpenAI, Shantanu Jain  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.  | Shantanu Jain | https://github.com/openai/tiktoken |
| tokenizers | 0.22.2 | Apache Software License | Nicolas Patry <patry.nicolas@protonmail.com>, Anthony Moi <anthony@huggingface.co> | https://github.com/huggingface/tokenizers |
| torch | 2.7.1 | BSD License | PyTorch Team | https://pytorch.org/ |
| tqdm | 4.67.1 | MIT License; Mozilla Public License 2.0 (MPL 2.0) | UNKNOWN | https://tqdm.github.io |
| transformers | 5.2.0 | Apache 2.0 License | The Hugging Face team (past and future) with the help of all our contributors (https://github.com/huggingface/transformers/graphs/contributors) | https://github.com/huggingface/transformers |
| trimesh | 4.12.2 | MIT License | Michael Dawson-Haggerty <mikedh@kerfed.com> | https://github.com/mikedh/trimesh |
| trio | 0.31.0 | MIT OR Apache-2.0 | "Nathaniel J. Smith" <njs@pobox.com> | https://github.com/python-trio/trio |
| trio-websocket | 0.12.2 | MIT License | Mark E. Haase | https://github.com/python-trio/trio-websocket |
| typer | 0.9.4 | MIT License | Sebastián Ramírez | https://github.com/tiangolo/typer |
| typer-slim | 0.21.2 | MIT | =?utf-8?q?Sebasti=C3=A1n_Ram=C3=ADrez?= <tiangolo@gmail.com> | https://github.com/fastapi/typer |
| typing-inspection | 0.4.2 | MIT | Victorien Plot <contact@vctrn.dev> | https://github.com/pydantic/typing-inspection |
| typing_extensions | 4.15.0 | PSF-2.0 | "Guido van Rossum, Jukka Lehtosalo, Łukasz Langa, Michael Lee" <levkivskyi@gmail.com> | https://github.com/python/typing_extensions |
| tzdata | 2025.3 | Apache-2.0 | Python Software Foundation | https://github.com/python/tzdata |
| urllib3 | 2.6.3 | MIT | Andrey Petrov <andrey.petrov@shazow.net> | https://github.com/urllib3/urllib3/blob/main/CHANGES.rst |
| uvicorn | 0.27.1 | BSD-3-Clause | Tom Christie <tom@tomchristie.com> | https://www.uvicorn.org/ |
| uvloop | 0.22.1 | Apache Software License; MIT License | Yury Selivanov <yury@magic.io> | UNKNOWN |
| watchfiles | 1.1.1 | MIT License | Samuel Colvin <s@muelcolvin.com> | https://github.com/samuelcolvin/watchfiles |
| websocket-client | 1.9.0 | Apache Software License | liris | https://github.com/websocket-client/websocket-client.git |
| websockets | 15.0.1 | BSD License | Aymeric Augustin <aymeric.augustin@m4x.org> | https://github.com/python-websockets/websockets |
| wrapt | 2.0.1 | Copyright (c) 2013-2025, Graham Dumpleton All rights reserved.  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:  * Redistributions of source code must retain the above copyright notice, this   list of conditions and the following disclaimer.  * Redistributions in binary form must reproduce the above copyright notice,   this list of conditions and the following disclaimer in the documentation   and/or other materials provided with the distribution.  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  | Graham Dumpleton | https://github.com/GrahamDumpleton/wrapt |
| wsproto | 1.2.0 | MIT License | Benno Rice | https://github.com/python-hyper/wsproto/ |
| xxhash | 3.7.0 | BSD License | Yue Du | https://github.com/ifduyue/python-xxhash |
| yarl | 1.24.2 | Apache-2.0 | Andrew Svetlov | https://github.com/aio-libs/yarl |
| zipp | 4.1.0 | MIT | "Jason R. Coombs" <jaraco@jaraco.com> | https://github.com/jaraco/zipp |

## Frontend dependencies

The web UI is built with Vite/Vue. Production bundles include **582** npm packages (direct and transitive).

| Module | License | Repository |
|--------|---------|------------|
| @ai-sdk/gateway@3.0.110 | Apache-2.0 | https://github.com/vercel/ai |
| @ai-sdk/provider-utils@4.0.26 | Apache-2.0 | https://github.com/vercel/ai |
| @ai-sdk/provider@3.0.10 | Apache-2.0 | https://github.com/vercel/ai |
| @babel/code-frame@7.29.0 | MIT | https://github.com/babel/babel |
| @babel/compat-data@7.29.3 | MIT | https://github.com/babel/babel |
| @babel/core@7.29.0 | MIT | https://github.com/babel/babel |
| @babel/generator@7.29.1 | MIT | https://github.com/babel/babel |
| @babel/helper-annotate-as-pure@7.27.3 | MIT | https://github.com/babel/babel |
| @babel/helper-compilation-targets@7.28.6 | MIT | https://github.com/babel/babel |
| @babel/helper-create-class-features-plugin@7.29.3 | MIT | https://github.com/babel/babel |
| @babel/helper-globals@7.28.0 | MIT | https://github.com/babel/babel |
| @babel/helper-member-expression-to-functions@7.28.5 | MIT | https://github.com/babel/babel |
| @babel/helper-module-imports@7.28.6 | MIT | https://github.com/babel/babel |
| @babel/helper-module-transforms@7.28.6 | MIT | https://github.com/babel/babel |
| @babel/helper-optimise-call-expression@7.27.1 | MIT | https://github.com/babel/babel |
| @babel/helper-plugin-utils@7.28.6 | MIT | https://github.com/babel/babel |
| @babel/helper-replace-supers@7.28.6 | MIT | https://github.com/babel/babel |
| @babel/helper-skip-transparent-expression-wrappers@7.27.1 | MIT | https://github.com/babel/babel |
| @babel/helper-string-parser@7.27.1 | MIT | https://github.com/babel/babel |
| @babel/helper-validator-identifier@7.28.5 | MIT | https://github.com/babel/babel |
| @babel/helper-validator-option@7.27.1 | MIT | https://github.com/babel/babel |
| @babel/helpers@7.29.2 | MIT | https://github.com/babel/babel |
| @babel/parser@7.28.6 | MIT | https://github.com/babel/babel |
| @babel/parser@7.29.3 | MIT | https://github.com/babel/babel |
| @babel/parser@8.0.0-alpha.12 | MIT | https://github.com/babel/babel |
| @babel/plugin-syntax-jsx@7.28.6 | MIT | https://github.com/babel/babel |
| @babel/plugin-syntax-typescript@7.28.6 | MIT | https://github.com/babel/babel |
| @babel/plugin-transform-modules-commonjs@7.28.6 | MIT | https://github.com/babel/babel |
| @babel/plugin-transform-typescript@7.28.6 | MIT | https://github.com/babel/babel |
| @babel/preset-typescript@7.28.5 | MIT | https://github.com/babel/babel |
| @babel/template@7.28.6 | MIT | https://github.com/babel/babel |
| @babel/traverse@7.29.0 | MIT | https://github.com/babel/babel |
| @babel/types@7.29.0 | MIT | https://github.com/babel/babel |
| @css-render/plugin-bem@0.15.14 | MIT | https://github.com/07akioni/css-render |
| @css-render/vue3-ssr@0.15.14 | MIT |  |
| @dotenvx/dotenvx@1.65.0 | BSD-3-Clause | https://github.com/dotenvx/dotenvx |
| @ecies/ciphers@0.2.6 | MIT | https://github.com/ecies/js-ciphers |
| @emotion/hash@0.8.0 | MIT | https://github.com/emotion-js/emotion/tree/master/packages/hash |
| @eslint-community/eslint-utils@4.9.1 | MIT | https://github.com/eslint-community/eslint-utils |
| @eslint-community/regexpp@4.12.2 | MIT | https://github.com/eslint-community/regexpp |
| @eslint/config-array@0.23.5 | Apache-2.0 | https://github.com/eslint/rewrite |
| @eslint/config-helpers@0.5.5 | Apache-2.0 | https://github.com/eslint/rewrite |
| @eslint/core@1.2.1 | Apache-2.0 | https://github.com/eslint/rewrite |
| @eslint/object-schema@3.0.5 | Apache-2.0 | https://github.com/eslint/rewrite |
| @eslint/plugin-kit@0.7.1 | Apache-2.0 | https://github.com/eslint/rewrite |
| @floating-ui/core@1.7.5 | MIT | https://github.com/floating-ui/floating-ui |
| @floating-ui/dom@1.7.6 | MIT | https://github.com/floating-ui/floating-ui |
| @floating-ui/utils@0.2.11 | MIT | https://github.com/floating-ui/floating-ui |
| @floating-ui/vue@1.1.11 | MIT | https://github.com/floating-ui/floating-ui |
| @hono/node-server@1.19.14 | MIT | https://github.com/honojs/node-server |
| @humanfs/core@0.19.2 | Apache-2.0 | https://github.com/humanwhocodes/humanfs |
| @humanfs/node@0.16.8 | Apache-2.0 | https://github.com/humanwhocodes/humanfs |
| @humanfs/types@0.15.0 | Apache-2.0 | https://github.com/humanwhocodes/humanfs |
| @humanwhocodes/module-importer@1.0.1 | Apache-2.0 | https://github.com/humanwhocodes/module-importer |
| @humanwhocodes/retry@0.4.3 | Apache-2.0 | https://github.com/humanwhocodes/retry |
| @internationalized/date@3.12.1 | Apache-2.0 | https://github.com/adobe/react-spectrum/tree/main/packages/@internationalized/date |
| @internationalized/number@3.6.6 | Apache-2.0 | https://github.com/adobe/react-spectrum |
| @intlify/core-base@11.4.0 | MIT | https://github.com/intlify/vue-i18n |
| @intlify/devtools-types@11.4.0 | MIT | https://github.com/intlify/vue-i18n |
| @intlify/message-compiler@11.4.0 | MIT | https://github.com/intlify/vue-i18n |
| @intlify/shared@11.4.0 | MIT | https://github.com/intlify/vue-i18n |
| @isaacs/cliui@9.0.0 | BlueOak-1.0.0 | https://github.com/isaacs/cliui |
| @jridgewell/gen-mapping@0.3.13 | MIT | https://github.com/jridgewell/sourcemaps |
| @jridgewell/remapping@2.3.5 | MIT | https://github.com/jridgewell/sourcemaps |
| @jridgewell/resolve-uri@3.1.2 | MIT | https://github.com/jridgewell/resolve-uri |
| @jridgewell/sourcemap-codec@1.5.5 | MIT | https://github.com/jridgewell/sourcemaps |
| @jridgewell/trace-mapping@0.3.31 | MIT | https://github.com/jridgewell/sourcemaps |
| @juggle/resize-observer@3.4.0 | Apache-2.0 | https://github.com/juggle/resize-observer |
| @markmend/ast@0.7.2 | MIT | https://github.com/jinghaihan/vue-stream-markdown |
| @markmend/core@0.7.2 | MIT | https://github.com/jinghaihan/vue-stream-markdown |
| @modelcontextprotocol/sdk@1.29.0 | MIT | https://github.com/modelcontextprotocol/typescript-sdk |
| @noble/ciphers@1.3.0 | MIT | https://github.com/paulmillr/noble-ciphers |
| @noble/curves@1.9.7 | MIT | https://github.com/paulmillr/noble-curves |
| @noble/hashes@1.8.0 | MIT | https://github.com/paulmillr/noble-hashes |
| @nodelib/fs.scandir@2.1.5 | MIT | https://github.com/nodelib/nodelib/tree/master/packages/fs/fs.scandir |
| @nodelib/fs.stat@2.0.5 | MIT | https://github.com/nodelib/nodelib/tree/master/packages/fs/fs.stat |
| @nodelib/fs.walk@1.2.8 | MIT | https://github.com/nodelib/nodelib/tree/master/packages/fs/fs.walk |
| @opentelemetry/api@1.9.0 | Apache-2.0 | https://github.com/open-telemetry/opentelemetry-js |
| @standard-schema/spec@1.1.0 | MIT | https://github.com/standard-schema/standard-schema |
| @swc/helpers@0.5.21 | Apache-2.0 | https://github.com/swc-project/swc |
| @tanstack/virtual-core@3.14.0 | MIT | https://github.com/TanStack/virtual |
| @tanstack/vue-virtual@3.13.24 | MIT | https://github.com/TanStack/virtual |
| @ts-morph/common@0.28.1 | MIT | https://github.com/dsherret/ts-morph |
| @types/debug@4.1.13 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/esrecurse@4.3.1 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/estree@1.0.8 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/hast@3.0.4 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/json-schema@7.0.15 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/katex@0.16.8 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/lodash-es@4.17.12 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/lodash@4.17.23 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/mdast@4.0.4 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/ms@2.1.0 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/unist@3.0.3 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @types/web-bluetooth@0.0.21 | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped |
| @unovue/detypes@0.8.5 | MIT | https://github.com/unovue/detypes |
| @vercel/oidc@3.2.0 | Apache-2.0 | https://github.com/vercel/vercel |
| @vicons/ionicons5@0.13.0 | MIT |  |
| @vue/compiler-core@3.5.27 | MIT | https://github.com/vuejs/core |
| @vue/compiler-dom@3.5.27 | MIT | https://github.com/vuejs/core |
| @vue/compiler-sfc@3.5.27 | MIT | https://github.com/vuejs/core |
| @vue/compiler-ssr@3.5.27 | MIT | https://github.com/vuejs/core |
| @vue/devtools-api@6.6.4 | MIT | https://github.com/vuejs/vue-devtools |
| @vue/devtools-api@7.7.9 | MIT | https://github.com/vuejs/devtools |
| @vue/devtools-kit@7.7.9 | MIT | https://github.com/vuejs/devtools |
| @vue/devtools-shared@7.7.9 | MIT | https://github.com/vuejs/devtools |
| @vue/reactivity@3.5.27 | MIT | https://github.com/vuejs/core |
| @vue/runtime-core@3.5.27 | MIT | https://github.com/vuejs/core |
| @vue/runtime-dom@3.5.27 | MIT | https://github.com/vuejs/core |
| @vue/server-renderer@3.5.27 | MIT | https://github.com/vuejs/core |
| @vue/shared@3.5.27 | MIT | https://github.com/vuejs/core |
| @vuedx/template-ast-types@0.7.1 | MIT | https://github.com/znck/vue-developer-experience |
| @vueuse/core@14.3.0 | MIT | https://github.com/vueuse/vueuse |
| @vueuse/metadata@14.3.0 | MIT | https://github.com/vueuse/vueuse |
| @vueuse/shared@14.3.0 | MIT | https://github.com/vueuse/vueuse |
| accepts@2.0.0 | MIT | https://github.com/jshttp/accepts |
| acorn-jsx@5.3.2 | MIT | https://github.com/acornjs/acorn-jsx |
| acorn@8.16.0 | MIT | https://github.com/acornjs/acorn |
| ai@6.0.175 | Apache-2.0 | https://github.com/vercel/ai |
| ajv-formats@3.0.1 | MIT | https://github.com/ajv-validator/ajv-formats |
| ajv@6.15.0 | MIT | https://github.com/ajv-validator/ajv |
| ajv@8.20.0 | MIT | https://github.com/ajv-validator/ajv |
| ansi-regex@5.0.1 | MIT | https://github.com/chalk/ansi-regex |
| ansi-regex@6.2.2 | MIT | https://github.com/chalk/ansi-regex |
| ansi-styles@4.3.0 | MIT | https://github.com/chalk/ansi-styles |
| aria-hidden@1.2.6 | MIT | https://github.com/theKashey/aria-hidden |
| ast-types-x@1.18.0 | MIT | https://github.com/pionxzh/ast-types-x |
| astral-regex@2.0.0 | MIT | https://github.com/kevva/astral-regex |
| async-validator@4.2.5 | MIT | https://github.com/yiminghe/async-validator |
| asynckit@0.4.0 | MIT | https://github.com/alexindigo/asynckit |
| atob@2.1.2 | (MIT OR Apache-2.0) | git://git.coolaj86.com/coolaj86/atob.js |
| axios@1.13.3 | MIT | https://github.com/axios/axios |
| balanced-match@1.0.2 | MIT | https://github.com/juliangruber/balanced-match |
| balanced-match@4.0.4 | MIT | https://github.com/juliangruber/balanced-match |
| baseline-browser-mapping@2.10.27 | Apache-2.0 | https://github.com/web-platform-dx/baseline-browser-mapping |
| birpc@2.9.0 | MIT | https://github.com/antfu-collective/birpc |
| body-parser@2.2.2 | MIT | https://github.com/expressjs/body-parser |
| boolbase@1.0.0 | ISC | https://github.com/fb55/boolbase |
| brace-expansion@1.1.14 | MIT | https://github.com/juliangruber/brace-expansion |
| brace-expansion@5.0.5 | MIT | https://github.com/juliangruber/brace-expansion |
| braces@3.0.3 | MIT | https://github.com/micromatch/braces |
| browserslist@4.28.2 | MIT | https://github.com/browserslist/browserslist |
| bundle-name@4.1.0 | MIT | https://github.com/sindresorhus/bundle-name |
| bytes@3.1.2 | MIT | https://github.com/visionmedia/bytes.js |
| c12@3.3.4 | MIT | https://github.com/unjs/c12 |
| call-bind-apply-helpers@1.0.2 | MIT | https://github.com/ljharb/call-bind-apply-helpers |
| call-bound@1.0.4 | MIT | https://github.com/ljharb/call-bound |
| caniuse-lite@1.0.30001791 | CC-BY-4.0 | https://github.com/browserslist/caniuse-lite |
| ccount@2.0.1 | MIT | https://github.com/wooorm/ccount |
| chalk@5.6.2 | MIT | https://github.com/chalk/chalk |
| character-entities@2.0.2 | MIT | https://github.com/wooorm/character-entities |
| chokidar@5.0.0 | MIT | https://github.com/paulmillr/chokidar |
| citty@0.2.2 | MIT | https://github.com/unjs/citty |
| class-variance-authority@0.7.1 | Apache-2.0 | https://github.com/joe-bell/cva |
| cli-cursor@5.0.0 | MIT | https://github.com/sindresorhus/cli-cursor |
| cli-progress@3.12.0 | MIT | https://github.com/npkgz/cli-progress |
| cli-spinners@3.4.0 | MIT | https://github.com/sindresorhus/cli-spinners |
| clsx@2.1.1 | MIT | https://github.com/lukeed/clsx |
| code-block-writer@13.0.3 | MIT | https://github.com/dsherret/code-block-writer |
| color-convert@2.0.1 | MIT | https://github.com/Qix-/color-convert |
| color-name@1.1.4 | MIT | https://github.com/colorjs/color-name |
| combined-stream@1.0.8 | MIT | https://github.com/felixge/node-combined-stream |
| commander@11.1.0 | MIT | https://github.com/tj/commander.js |
| commander@14.0.3 | MIT | https://github.com/tj/commander.js |
| commander@8.3.0 | MIT | https://github.com/tj/commander.js |
| concat-map@0.0.1 | MIT | https://github.com/substack/node-concat-map |
| confbox@0.2.4 | MIT | https://github.com/unjs/confbox |
| consola@3.4.2 | MIT | https://github.com/unjs/consola |
| content-disposition@1.1.0 | MIT | https://github.com/jshttp/content-disposition |
| content-type@1.0.5 | MIT | https://github.com/jshttp/content-type |
| convert-hrtime@5.0.0 | MIT | https://github.com/sindresorhus/convert-hrtime |
| convert-source-map@2.0.0 | MIT | https://github.com/thlorenz/convert-source-map |
| cookie-signature@1.2.2 | MIT | https://github.com/visionmedia/node-cookie-signature |
| cookie@0.7.2 | MIT | https://github.com/jshttp/cookie |
| copy-anything@4.0.5 | MIT | https://github.com/mesqueeb/copy-anything |
| cors@2.8.6 | MIT | https://github.com/expressjs/cors |
| cross-spawn@7.0.6 | MIT | https://github.com/moxystudio/node-cross-spawn |
| css-render@0.15.14 | MIT | https://github.com/07akioni/css-render |
| css-select@5.2.2 | BSD-2-Clause | https://github.com/fb55/css-select |
| css-what@6.2.2 | BSD-2-Clause | https://github.com/fb55/css-what |
| css@3.0.0 | MIT | https://github.com/reworkcss/css |
| cssesc@3.0.0 | MIT | https://github.com/mathiasbynens/cssesc |
| csstype@3.0.11 | MIT | https://github.com/frenic/csstype |
| csstype@3.2.3 | MIT | https://github.com/frenic/csstype |
| date-fns-tz@3.2.0 | MIT | https://github.com/marnusw/date-fns-tz |
| date-fns@4.1.0 | MIT | https://github.com/date-fns/date-fns |
| debug@4.4.3 | MIT | https://github.com/debug-js/debug |
| decode-named-character-reference@1.3.0 | MIT | https://github.com/wooorm/decode-named-character-reference |
| decode-uri-component@0.2.2 | MIT | https://github.com/SamVerschueren/decode-uri-component |
| dedent@1.7.2 | MIT | https://github.com/dmnd/dedent |
| deep-diff@1.0.2 | MIT | https://github.com/flitbit/diff |
| deep-is@0.1.4 | MIT | https://github.com/thlorenz/deep-is |
| deepmerge@4.3.1 | MIT | https://github.com/TehShrike/deepmerge |
| default-browser-id@5.0.1 | MIT | https://github.com/sindresorhus/default-browser-id |
| default-browser@5.5.0 | MIT | https://github.com/sindresorhus/default-browser |
| define-lazy-prop@3.0.0 | MIT | https://github.com/sindresorhus/define-lazy-prop |
| defu@6.1.7 | MIT | https://github.com/unjs/defu |
| delayed-stream@1.0.0 | MIT | https://github.com/felixge/node-delayed-stream |
| depd@2.0.0 | MIT | https://github.com/dougwilson/nodejs-depd |
| dequal@2.0.3 | MIT | https://github.com/lukeed/dequal |
| destr@2.0.5 | MIT | https://github.com/unjs/destr |
| devlop@1.1.0 | MIT | https://github.com/wooorm/devlop |
| diff@8.0.4 | BSD-3-Clause | https://github.com/kpdecker/jsdiff |
| dom-serializer@2.0.0 | MIT | https://github.com/cheeriojs/dom-serializer |
| domelementtype@2.3.0 | BSD-2-Clause | https://github.com/fb55/domelementtype |
| domhandler@5.0.3 | BSD-2-Clause | https://github.com/fb55/domhandler |
| domutils@3.2.2 | BSD-2-Clause | https://github.com/fb55/domutils |
| dotenv@17.4.2 | BSD-2-Clause | https://github.com/motdotla/dotenv |
| dunder-proto@1.0.1 | MIT | https://github.com/es-shims/dunder-proto |
| eciesjs@0.4.18 | MIT | https://github.com/ecies/js |
| ee-first@1.1.1 | MIT | https://github.com/jonathanong/ee-first |
| electron-to-chromium@1.5.351 | ISC | https://github.com/Kilian/electron-to-chromium |
| emoji-regex@8.0.0 | MIT | https://github.com/mathiasbynens/emoji-regex |
| encodeurl@2.0.0 | MIT | https://github.com/pillarjs/encodeurl |
| entities@4.5.0 | BSD-2-Clause | https://github.com/fb55/entities |
| entities@7.0.1 | BSD-2-Clause | https://github.com/fb55/entities |
| es-define-property@1.0.1 | MIT | https://github.com/ljharb/es-define-property |
| es-errors@1.3.0 | MIT | https://github.com/ljharb/es-errors |
| es-object-atoms@1.1.1 | MIT | https://github.com/ljharb/es-object-atoms |
| es-set-tostringtag@2.1.0 | MIT | https://github.com/es-shims/es-set-tostringtag |
| escalade@3.2.0 | MIT | https://github.com/lukeed/escalade |
| escape-html@1.0.3 | MIT | https://github.com/component/escape-html |
| escape-string-regexp@4.0.0 | MIT | https://github.com/sindresorhus/escape-string-regexp |
| escape-string-regexp@5.0.0 | MIT | https://github.com/sindresorhus/escape-string-regexp |
| eslint-scope@9.1.2 | BSD-2-Clause | https://github.com/eslint/js |
| eslint-visitor-keys@3.4.3 | Apache-2.0 | https://github.com/eslint/eslint-visitor-keys |
| eslint-visitor-keys@5.0.1 | Apache-2.0 | https://github.com/eslint/js |
| eslint@10.3.0 | MIT | https://github.com/eslint/eslint |
| espree@11.2.0 | BSD-2-Clause | https://github.com/eslint/js |
| esquery@1.7.0 | BSD-3-Clause | https://github.com/estools/esquery |
| esrecurse@4.3.0 | BSD-2-Clause | https://github.com/estools/esrecurse |
| estraverse@5.3.0 | BSD-2-Clause | https://github.com/estools/estraverse |
| estree-walker@2.0.2 | MIT | https://github.com/Rich-Harris/estree-walker |
| esutils@2.0.3 | BSD-2-Clause | https://github.com/estools/esutils |
| etag@1.8.1 | MIT | https://github.com/jshttp/etag |
| eventsource-parser@3.0.8 | MIT | https://github.com/rexxars/eventsource-parser |
| eventsource@3.0.7 | MIT | git://git@github.com/EventSource/eventsource |
| evtd@0.2.4 | MIT |  |
| execa@5.1.1 | MIT | https://github.com/sindresorhus/execa |
| express-rate-limit@8.5.0 | MIT | https://github.com/express-rate-limit/express-rate-limit |
| express@5.2.1 | MIT | https://github.com/expressjs/express |
| exsolve@1.0.8 | MIT | https://github.com/unjs/exsolve |
| fast-deep-equal@3.1.3 | MIT | https://github.com/epoberezkin/fast-deep-equal |
| fast-diff@1.3.0 | Apache-2.0 | https://github.com/jhchen/fast-diff |
| fast-glob@3.3.3 | MIT | https://github.com/mrmlnc/fast-glob |
| fast-json-stable-stringify@2.1.0 | MIT | https://github.com/epoberezkin/fast-json-stable-stringify |
| fast-levenshtein@2.0.6 | MIT | https://github.com/hiddentao/fast-levenshtein |
| fast-uri@3.1.2 | BSD-3-Clause | https://github.com/fastify/fast-uri |
| fastq@1.20.1 | ISC | https://github.com/mcollina/fastq |
| fault@2.0.1 | MIT | https://github.com/wooorm/fault |
| fdir@6.5.0 | MIT | https://github.com/thecodrr/fdir |
| file-entry-cache@8.0.0 | MIT | https://github.com/jaredwray/file-entry-cache |
| fill-range@7.1.1 | MIT | https://github.com/jonschlinkert/fill-range |
| finalhandler@2.1.1 | MIT | https://github.com/pillarjs/finalhandler |
| find-up@5.0.0 | MIT | https://github.com/sindresorhus/find-up |
| flat-cache@4.0.1 | MIT | https://github.com/jaredwray/flat-cache |
| flatted@3.4.2 | ISC | https://github.com/WebReflection/flatted |
| follow-redirects@1.15.11 | MIT | https://github.com/follow-redirects/follow-redirects |
| foreground-child@3.3.1 | ISC | https://github.com/tapjs/foreground-child |
| form-data@4.0.5 | MIT | https://github.com/form-data/form-data |
| format@0.2.2 | MIT | https://github.com/samsonjs/format |
| forwarded@0.2.0 | MIT | https://github.com/jshttp/forwarded |
| framer-motion@12.38.0 | MIT | https://github.com/motiondivision/motion |
| fresh@2.0.0 | MIT | https://github.com/jshttp/fresh |
| frontend@0.0.0 | UNLICENSED |  |
| fs-extra@11.3.4 | MIT | https://github.com/jprichardson/node-fs-extra |
| fs.realpath@1.0.0 | ISC | https://github.com/isaacs/fs.realpath |
| function-bind@1.1.2 | MIT | https://github.com/Raynos/function-bind |
| function-timeout@1.0.2 | MIT | https://github.com/sindresorhus/function-timeout |
| fuzzysort@3.1.0 | MIT | https://github.com/farzher/fuzzysort |
| gensync@1.0.0-beta.2 | MIT | https://github.com/loganfsmyth/gensync |
| get-east-asian-width@1.5.0 | MIT | https://github.com/sindresorhus/get-east-asian-width |
| get-intrinsic@1.3.0 | MIT | https://github.com/ljharb/get-intrinsic |
| get-own-enumerable-keys@1.0.0 | MIT | https://github.com/sindresorhus/get-own-enumerable-keys |
| get-proto@1.0.1 | MIT | https://github.com/ljharb/get-proto |
| get-stream@6.0.1 | MIT | https://github.com/sindresorhus/get-stream |
| get-tsconfig@4.14.0 | MIT | https://github.com/privatenumber/get-tsconfig |
| giget@3.2.0 | MIT | https://github.com/unjs/giget |
| glob-parent@5.1.2 | ISC | https://github.com/gulpjs/glob-parent |
| glob-parent@6.0.2 | ISC | https://github.com/gulpjs/glob-parent |
| glob@11.1.0 | BlueOak-1.0.0 | https://github.com/isaacs/node-glob |
| glob@7.2.3 | ISC | https://github.com/isaacs/node-glob |
| gonzales-pe@4.3.0 | MIT | https://github.com/tonyganch/gonzales-pe |
| gopd@1.2.0 | MIT | https://github.com/ljharb/gopd |
| graceful-fs@4.2.11 | ISC | https://github.com/isaacs/node-graceful-fs |
| has-symbols@1.1.0 | MIT | https://github.com/inspect-js/has-symbols |
| has-tostringtag@1.0.2 | MIT | https://github.com/inspect-js/has-tostringtag |
| hasown@2.0.2 | MIT | https://github.com/inspect-js/hasOwn |
| he@1.2.0 | MIT | https://github.com/mathiasbynens/he |
| hey-listen@1.0.8 | MIT | https://github.com/Popmotion/hey-listen |
| highlight.js@11.11.1 | BSD-3-Clause | https://github.com/highlightjs/highlight.js |
| hono@4.12.17 | MIT | https://github.com/honojs/hono |
| hookable@5.5.3 | MIT | https://github.com/unjs/hookable |
| http-errors@2.0.1 | MIT | https://github.com/jshttp/http-errors |
| human-signals@2.1.0 | Apache-2.0 | https://github.com/ehmicky/human-signals |
| iconv-lite@0.7.2 | MIT | https://github.com/pillarjs/iconv-lite |
| identifier-regex@1.0.1 | MIT | https://github.com/sindresorhus/identifier-regex |
| ignore@5.3.2 | MIT | https://github.com/kaelzhang/node-ignore |
| imurmurhash@0.1.4 | MIT | https://github.com/jensyt/imurmurhash-js |
| inflight@1.0.6 | ISC | https://github.com/npm/inflight |
| inherits@2.0.4 | ISC | https://github.com/isaacs/inherits |
| ip-address@10.1.0 | MIT | https://github.com/beaugunderson/ip-address |
| ipaddr.js@1.9.1 | MIT | https://github.com/whitequark/ipaddr.js |
| is-docker@3.0.0 | MIT | https://github.com/sindresorhus/is-docker |
| is-extglob@2.1.1 | MIT | https://github.com/jonschlinkert/is-extglob |
| is-fullwidth-code-point@3.0.0 | MIT | https://github.com/sindresorhus/is-fullwidth-code-point |
| is-glob@4.0.3 | MIT | https://github.com/micromatch/is-glob |
| is-identifier@1.0.1 | MIT | https://github.com/sindresorhus/is-identifier |
| is-inside-container@1.0.0 | MIT | https://github.com/sindresorhus/is-inside-container |
| is-interactive@2.0.0 | MIT | https://github.com/sindresorhus/is-interactive |
| is-number@7.0.0 | MIT | https://github.com/jonschlinkert/is-number |
| is-obj@3.0.0 | MIT | https://github.com/sindresorhus/is-obj |
| is-promise@4.0.0 | MIT | https://github.com/then/is-promise |
| is-regexp@3.1.0 | MIT | https://github.com/sindresorhus/is-regexp |
| is-stream@2.0.1 | MIT | https://github.com/sindresorhus/is-stream |
| is-unicode-supported@2.1.0 | MIT | https://github.com/sindresorhus/is-unicode-supported |
| is-what@5.5.0 | MIT | https://github.com/mesqueeb/is-what |
| is-wsl@3.1.1 | MIT | https://github.com/sindresorhus/is-wsl |
| isexe@2.0.0 | ISC | https://github.com/isaacs/isexe |
| isexe@3.1.5 | BlueOak-1.0.0 | https://github.com/isaacs/isexe |
| jackspeak@4.2.3 | BlueOak-1.0.0 | https://github.com/isaacs/jackspeak |
| jiti@2.7.0 | MIT | https://github.com/unjs/jiti |
| jose@6.2.3 | MIT | https://github.com/panva/jose |
| js-tokens@4.0.0 | MIT | https://github.com/lydell/js-tokens |
| jsesc@3.1.0 | MIT | https://github.com/mathiasbynens/jsesc |
| json-buffer@3.0.1 | MIT | https://github.com/dominictarr/json-buffer |
| json-schema-traverse@0.4.1 | MIT | https://github.com/epoberezkin/json-schema-traverse |
| json-schema-traverse@1.0.0 | MIT | https://github.com/epoberezkin/json-schema-traverse |
| json-schema-typed@8.0.2 | BSD-2-Clause | https://github.com/RemyRylan/json-schema-typed |
| json-schema@0.4.0 | (AFL-2.1 OR BSD-3-Clause) | https://github.com/kriszyp/json-schema |
| json-stable-stringify-without-jsonify@1.0.1 | MIT | https://github.com/samn/json-stable-stringify |
| json5@2.2.3 | MIT | https://github.com/json5/json5 |
| jsonfile@6.2.1 | MIT | https://github.com/jprichardson/node-jsonfile |
| katex@0.16.45 | MIT | https://github.com/KaTeX/KaTeX |
| keyv@4.5.4 | MIT | https://github.com/jaredwray/keyv |
| kleur@3.0.3 | MIT | https://github.com/lukeed/kleur |
| levn@0.4.1 | MIT | https://github.com/gkz/levn |
| locate-path@6.0.0 | MIT | https://github.com/sindresorhus/locate-path |
| lodash-es@4.17.23 | MIT | https://github.com/lodash/lodash |
| lodash.sortedlastindex@4.1.0 | MIT | https://github.com/lodash/lodash |
| lodash.truncate@4.4.2 | MIT | https://github.com/lodash/lodash |
| lodash@4.17.23 | MIT | https://github.com/lodash/lodash |
| log-symbols@7.0.1 | MIT | https://github.com/sindresorhus/log-symbols |
| longest-streak@3.1.0 | MIT | https://github.com/wooorm/longest-streak |
| lru-cache@11.3.6 | BlueOak-1.0.0 | https://github.com/isaacs/node-lru-cache |
| lru-cache@5.1.1 | ISC | https://github.com/isaacs/node-lru-cache |
| lucide-vue-next@1.0.0 | ISC | https://github.com/lucide-icons/lucide |
| magic-string@0.30.21 | MIT | https://github.com/Rich-Harris/magic-string |
| make-asynchronous@1.1.0 | MIT | https://github.com/sindresorhus/make-asynchronous |
| markdown-table@3.0.4 | MIT | https://github.com/wooorm/markdown-table |
| marked@18.0.3 | MIT | https://github.com/markedjs/marked |
| math-intrinsics@1.1.0 | MIT | https://github.com/es-shims/math-intrinsics |
| mdast-util-find-and-replace@3.0.2 | MIT | https://github.com/syntax-tree/mdast-util-find-and-replace |
| mdast-util-from-markdown@2.0.3 | MIT | https://github.com/syntax-tree/mdast-util-from-markdown |
| mdast-util-frontmatter@2.0.1 | MIT | https://github.com/syntax-tree/mdast-util-frontmatter |
| mdast-util-gfm-autolink-literal@2.0.1 | MIT | https://github.com/syntax-tree/mdast-util-gfm-autolink-literal |
| mdast-util-gfm-footnote@2.1.0 | MIT | https://github.com/syntax-tree/mdast-util-gfm-footnote |
| mdast-util-gfm-strikethrough@2.0.0 | MIT | https://github.com/syntax-tree/mdast-util-gfm-strikethrough |
| mdast-util-gfm-table@2.0.0 | MIT | https://github.com/syntax-tree/mdast-util-gfm-table |
| mdast-util-gfm-task-list-item@2.0.0 | MIT | https://github.com/syntax-tree/mdast-util-gfm-task-list-item |
| mdast-util-gfm@3.1.0 | MIT | https://github.com/syntax-tree/mdast-util-gfm |
| mdast-util-math@3.0.0 | MIT | https://github.com/syntax-tree/mdast-util-math |
| mdast-util-phrasing@4.1.0 | MIT | https://github.com/syntax-tree/mdast-util-phrasing |
| mdast-util-to-markdown@2.1.2 | MIT | https://github.com/syntax-tree/mdast-util-to-markdown |
| mdast-util-to-string@4.0.0 | MIT | https://github.com/syntax-tree/mdast-util-to-string |
| media-typer@1.1.0 | MIT | https://github.com/jshttp/media-typer |
| merge-descriptors@2.0.0 | MIT | https://github.com/sindresorhus/merge-descriptors |
| merge-stream@2.0.0 | MIT | https://github.com/grncdr/merge-stream |
| merge2@1.4.1 | MIT | https://github.com/teambition/merge2 |
| micromark-core-commonmark@2.0.3 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-core-commonmark |
| micromark-extension-cjk-friendly-gfm-strikethrough@2.0.1 | MIT | https://github.com/tats-u/markdown-cjk-friendly |
| micromark-extension-cjk-friendly-util@3.0.1 | MIT | https://github.com/tats-u/markdown-cjk-friendly |
| micromark-extension-cjk-friendly@2.0.1 | MIT | https://github.com/tats-u/markdown-cjk-friendly |
| micromark-extension-frontmatter@2.0.0 | MIT | https://github.com/micromark/micromark-extension-frontmatter |
| micromark-extension-gfm-autolink-literal@2.1.0 | MIT | https://github.com/micromark/micromark-extension-gfm-autolink-literal |
| micromark-extension-gfm-footnote@2.1.0 | MIT | https://github.com/micromark/micromark-extension-gfm-footnote |
| micromark-extension-gfm-strikethrough@2.1.0 | MIT | https://github.com/micromark/micromark-extension-gfm-strikethrough |
| micromark-extension-gfm-table@2.1.1 | MIT | https://github.com/micromark/micromark-extension-gfm-table |
| micromark-extension-gfm-tagfilter@2.0.0 | MIT | https://github.com/micromark/micromark-extension-gfm-tagfilter |
| micromark-extension-gfm-task-list-item@2.1.0 | MIT | https://github.com/micromark/micromark-extension-gfm-task-list-item |
| micromark-extension-gfm@3.0.0 | MIT | https://github.com/micromark/micromark-extension-gfm |
| micromark-extension-math@3.1.0 | MIT | https://github.com/micromark/micromark-extension-math |
| micromark-factory-destination@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-factory-destination |
| micromark-factory-label@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-factory-label |
| micromark-factory-space@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-factory-space |
| micromark-factory-title@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-factory-title |
| micromark-factory-whitespace@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-factory-whitespace |
| micromark-util-character@2.1.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-character |
| micromark-util-chunked@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-chunked |
| micromark-util-classify-character@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-classify-character |
| micromark-util-combine-extensions@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-combine-extensions |
| micromark-util-decode-numeric-character-reference@2.0.2 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-decode-numeric-character-reference |
| micromark-util-decode-string@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-decode-string |
| micromark-util-encode@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-encode |
| micromark-util-html-tag-name@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-html-tag-name |
| micromark-util-normalize-identifier@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-normalize-identifier |
| micromark-util-resolve-all@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-resolve-all |
| micromark-util-sanitize-uri@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-sanitize-uri |
| micromark-util-subtokenize@2.1.0 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-subtokenize |
| micromark-util-symbol@2.0.1 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-symbol |
| micromark-util-types@2.0.2 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark-util-types |
| micromark@4.0.2 | MIT | https://github.com/micromark/micromark/tree/main/packages/micromark |
| micromatch@4.0.8 | MIT | https://github.com/micromatch/micromatch |
| mime-db@1.52.0 | MIT | https://github.com/jshttp/mime-db |
| mime-db@1.54.0 | MIT | https://github.com/jshttp/mime-db |
| mime-types@2.1.35 | MIT | https://github.com/jshttp/mime-types |
| mime-types@3.0.2 | MIT | https://github.com/jshttp/mime-types |
| mimic-fn@2.1.0 | MIT | https://github.com/sindresorhus/mimic-fn |
| mimic-function@5.0.1 | MIT | https://github.com/sindresorhus/mimic-function |
| minimatch@10.2.5 | BlueOak-1.0.0 | https://github.com/isaacs/minimatch |
| minimatch@3.1.5 | ISC | https://github.com/isaacs/minimatch |
| minimist@1.2.8 | MIT | https://github.com/minimistjs/minimist |
| minipass@7.1.3 | BlueOak-1.0.0 | https://github.com/isaacs/minipass |
| mitt@3.0.1 | MIT | https://github.com/developit/mitt |
| motion-dom@12.38.0 | MIT | https://github.com/motiondivision/motion |
| motion-utils@12.36.0 | MIT | https://github.com/motiondivision/motion |
| motion-v@2.2.1 | MIT | https://github.com/motiondivision/motion-vue |
| ms@2.1.3 | MIT | https://github.com/vercel/ms |
| naive-ui@2.43.2 | MIT | https://github.com/tusen-ai/naive-ui |
| nanoid@3.3.12 | MIT | https://github.com/ai/nanoid |
| nanoid@5.1.11 | MIT | https://github.com/ai/nanoid |
| natural-compare@1.4.0 | MIT | https://github.com/litejs/natural-compare-lite |
| negotiator@1.0.0 | MIT | https://github.com/jshttp/negotiator |
| node-fetch-native@1.6.7 | MIT | https://github.com/unjs/node-fetch-native |
| node-html-parser@7.1.0 | MIT | https://github.com/taoqf/node-fast-html-parser |
| node-releases@2.0.38 | MIT | https://github.com/chicoxyzzy/node-releases |
| npm-run-path@4.0.1 | MIT | https://github.com/sindresorhus/npm-run-path |
| nth-check@2.1.1 | BSD-2-Clause | https://github.com/fb55/nth-check |
| nypm@0.6.6 | MIT | https://github.com/unjs/nypm |
| object-assign@4.1.1 | MIT | https://github.com/sindresorhus/object-assign |
| object-inspect@1.13.4 | MIT | https://github.com/inspect-js/object-inspect |
| object-treeify@1.1.33 | MIT | https://github.com/blackflux/object-treeify |
| ofetch@1.5.1 | MIT | https://github.com/unjs/ofetch |
| ohash@2.0.11 | MIT | https://github.com/unjs/ohash |
| on-finished@2.4.1 | MIT | https://github.com/jshttp/on-finished |
| once@1.4.0 | ISC | https://github.com/isaacs/once |
| onetime@5.1.2 | MIT | https://github.com/sindresorhus/onetime |
| onetime@7.0.0 | MIT | https://github.com/sindresorhus/onetime |
| open@10.2.0 | MIT | https://github.com/sindresorhus/open |
| optionator@0.9.4 | MIT | https://github.com/gkz/optionator |
| ora@9.4.0 | MIT | https://github.com/sindresorhus/ora |
| p-event@6.0.1 | MIT | https://github.com/sindresorhus/p-event |
| p-limit@3.1.0 | MIT | https://github.com/sindresorhus/p-limit |
| p-locate@5.0.0 | MIT | https://github.com/sindresorhus/p-locate |
| p-timeout@6.1.4 | MIT | https://github.com/sindresorhus/p-timeout |
| package-json-from-dist@1.0.1 | BlueOak-1.0.0 | https://github.com/isaacs/package-json-from-dist |
| parseurl@1.3.3 | MIT | https://github.com/pillarjs/parseurl |
| path-browserify@1.0.1 | MIT | https://github.com/browserify/path-browserify |
| path-exists@4.0.0 | MIT | https://github.com/sindresorhus/path-exists |
| path-is-absolute@1.0.1 | MIT | https://github.com/sindresorhus/path-is-absolute |
| path-key@3.1.1 | MIT | https://github.com/sindresorhus/path-key |
| path-scurry@2.0.2 | BlueOak-1.0.0 | https://github.com/isaacs/path-scurry |
| path-to-regexp@8.4.2 | MIT | https://github.com/pillarjs/path-to-regexp |
| pathe@2.0.3 | MIT | https://github.com/unjs/pathe |
| perfect-debounce@1.0.0 | MIT | https://github.com/unjs/perfect-debounce |
| perfect-debounce@2.1.0 | MIT | https://github.com/unjs/perfect-debounce |
| picocolors@1.1.1 | ISC | https://github.com/alexeyraspopov/picocolors |
| picomatch@2.3.2 | MIT | https://github.com/micromatch/picomatch |
| picomatch@4.0.4 | MIT | https://github.com/micromatch/picomatch |
| pinia@3.0.4 | MIT | https://github.com/vuejs/pinia |
| pkce-challenge@5.0.1 | MIT | https://github.com/crouchcd/pkce-challenge |
| pkg-types@2.3.1 | MIT | https://github.com/unjs/pkg-types |
| postcss-less@6.0.0 | MIT | https://github.com/shellscape/postcss-less |
| postcss-sass@0.5.0 | MIT | https://github.com/AleshaOleg/postcss-sass |
| postcss-scss@4.0.9 | MIT | https://github.com/postcss/postcss-scss |
| postcss-selector-parser@7.1.1 | MIT | https://github.com/postcss/postcss-selector-parser |
| postcss-styl@0.12.3 | MIT | https://github.com/stylus/postcss-styl |
| postcss@8.5.6 | MIT | https://github.com/postcss/postcss |
| prelude-ls@1.2.1 | MIT | https://github.com/gkz/prelude-ls |
| prettier@3.8.3 | MIT | https://github.com/prettier/prettier |
| prompts@2.4.2 | MIT | https://github.com/terkelg/prompts |
| proxy-addr@2.0.7 | MIT | https://github.com/jshttp/proxy-addr |
| proxy-from-env@1.1.0 | MIT | https://github.com/Rob--W/proxy-from-env |
| punycode@2.3.1 | MIT | https://github.com/mathiasbynens/punycode.js |
| qs@6.15.1 | BSD-3-Clause | https://github.com/ljharb/qs |
| queue-microtask@1.2.3 | MIT | https://github.com/feross/queue-microtask |
| range-parser@1.2.1 | MIT | https://github.com/jshttp/range-parser |
| raw-body@3.0.2 | MIT | https://github.com/stream-utils/raw-body |
| rc9@3.0.1 | MIT | https://github.com/unjs/rc9 |
| readdirp@5.0.0 | MIT | https://github.com/paulmillr/readdirp |
| recast-x@1.0.5 | MIT | https://github.com/pionxzh/recast-x |
| reka-ui@2.9.7 | MIT | https://github.com/unovue/reka-ui |
| require-from-string@2.0.2 | MIT | https://github.com/floatdrop/require-from-string |
| reserved-identifiers@1.2.0 | MIT | https://github.com/sindresorhus/reserved-identifiers |
| resolve-pkg-maps@1.0.0 | MIT | https://github.com/privatenumber/resolve-pkg-maps |
| restore-cursor@5.1.0 | MIT | https://github.com/sindresorhus/restore-cursor |
| reusify@1.1.0 | MIT | https://github.com/mcollina/reusify |
| rfdc@1.4.1 | MIT | https://github.com/davidmarkclements/rfdc |
| router@2.2.0 | MIT | https://github.com/pillarjs/router |
| run-applescript@7.1.0 | MIT | https://github.com/sindresorhus/run-applescript |
| run-parallel@1.2.0 | MIT | https://github.com/feross/run-parallel |
| safer-buffer@2.1.2 | MIT | https://github.com/ChALkeR/safer-buffer |
| sax@1.2.4 | ISC | https://github.com/isaacs/sax-js |
| seemly@0.3.10 | MIT |  |
| semver@6.3.1 | ISC | https://github.com/npm/node-semver |
| semver@7.7.4 | ISC | https://github.com/npm/node-semver |
| send@1.2.1 | MIT | https://github.com/pillarjs/send |
| serve-static@2.2.1 | MIT | https://github.com/expressjs/serve-static |
| setprototypeof@1.2.0 | ISC | https://github.com/wesleytodd/setprototypeof |
| shadcn-vue@2.6.2 | MIT | https://github.com/unovue/shadcn-vue |
| shebang-command@2.0.0 | MIT | https://github.com/kevva/shebang-command |
| shebang-regex@3.0.0 | MIT | https://github.com/sindresorhus/shebang-regex |
| side-channel-list@1.0.1 | MIT | https://github.com/ljharb/side-channel-list |
| side-channel-map@1.0.1 | MIT | https://github.com/ljharb/side-channel-map |
| side-channel-weakmap@1.0.2 | MIT | https://github.com/ljharb/side-channel-weakmap |
| side-channel@1.1.0 | MIT | https://github.com/ljharb/side-channel |
| signal-exit@3.0.7 | ISC | https://github.com/tapjs/signal-exit |
| signal-exit@4.1.0 | ISC | https://github.com/tapjs/signal-exit |
| sisteransi@1.0.5 | MIT | https://github.com/terkelg/sisteransi |
| slice-ansi@4.0.0 | MIT | https://github.com/chalk/slice-ansi |
| source-map-js@1.2.1 | BSD-3-Clause | https://github.com/7rulnik/source-map-js |
| source-map-resolve@0.6.0 | MIT | https://github.com/lydell/source-map-resolve |
| source-map@0.6.1 | BSD-3-Clause | https://github.com/mozilla/source-map |
| source-map@0.7.6 | BSD-3-Clause | https://github.com/mozilla/source-map |
| speakingurl@14.0.1 | BSD-3-Clause | https://github.com/pid/speakingurl |
| statuses@2.0.2 | MIT | https://github.com/jshttp/statuses |
| stdin-discarder@0.3.2 | MIT | https://github.com/sindresorhus/stdin-discarder |
| string-width@4.2.3 | MIT | https://github.com/sindresorhus/string-width |
| string-width@8.2.1 | MIT | https://github.com/sindresorhus/string-width |
| stringify-object@6.0.0 | BSD-2-Clause | https://github.com/sindresorhus/stringify-object |
| strip-ansi@6.0.1 | MIT | https://github.com/chalk/strip-ansi |
| strip-ansi@7.2.0 | MIT | https://github.com/chalk/strip-ansi |
| strip-final-newline@2.0.0 | MIT | https://github.com/sindresorhus/strip-final-newline |
| stylus@0.57.0 | MIT | https://github.com/stylus/stylus |
| super-regex@1.1.0 | MIT | https://github.com/sindresorhus/super-regex |
| superjson@2.2.6 | MIT | https://github.com/blitz-js/superjson |
| table@6.9.0 | BSD-3-Clause | https://github.com/gajus/table |
| tailwind-merge@3.5.0 | MIT | https://github.com/dcastil/tailwind-merge |
| tailwindcss@4.2.4 | MIT | https://github.com/tailwindlabs/tailwindcss |
| time-span@5.1.0 | MIT | https://github.com/sindresorhus/time-span |
| tiny-invariant@1.3.3 | MIT | https://github.com/alexreardon/tiny-invariant |
| tinyexec@1.1.2 | MIT | https://github.com/tinylibs/tinyexec |
| tinyglobby@0.2.16 | MIT | https://github.com/SuperchupuDev/tinyglobby |
| to-regex-range@5.0.1 | MIT | https://github.com/micromatch/to-regex-range |
| toidentifier@1.0.1 | MIT | https://github.com/component/toidentifier |
| treemate@0.3.11 | MIT | https://github.com/07akioni/treemate |
| ts-morph@27.0.2 | MIT | https://github.com/dsherret/ts-morph |
| tslib@2.8.1 | 0BSD | https://github.com/Microsoft/tslib |
| tw-animate-css@1.4.0 | MIT | https://github.com/Wombosvideo/tw-animate-css |
| type-check@0.4.0 | MIT | https://github.com/gkz/type-check |
| type-fest@4.41.0 | (MIT OR CC0-1.0) | https://github.com/sindresorhus/type-fest |
| type-is@2.0.1 | MIT | https://github.com/jshttp/type-is |
| typescript@5.9.3 | Apache-2.0 | https://github.com/microsoft/TypeScript |
| ufo@1.6.4 | MIT | https://github.com/unjs/ufo |
| undici@7.25.0 | MIT | https://github.com/nodejs/undici |
| unist-util-is@6.0.1 | MIT | https://github.com/syntax-tree/unist-util-is |
| unist-util-remove-position@5.0.0 | MIT | https://github.com/syntax-tree/unist-util-remove-position |
| unist-util-stringify-position@4.0.0 | MIT | https://github.com/syntax-tree/unist-util-stringify-position |
| unist-util-visit-parents@6.0.2 | MIT | https://github.com/syntax-tree/unist-util-visit-parents |
| unist-util-visit@5.1.0 | MIT | https://github.com/syntax-tree/unist-util-visit |
| universalify@2.0.1 | MIT | https://github.com/RyanZim/universalify |
| unpipe@1.0.0 | MIT | https://github.com/stream-utils/unpipe |
| update-browserslist-db@1.2.3 | MIT | https://github.com/browserslist/update-db |
| uri-js@4.4.1 | BSD-2-Clause | https://github.com/garycourt/uri-js |
| util-deprecate@1.0.2 | MIT | https://github.com/TooTallNate/util-deprecate |
| validate-npm-package-name@5.0.1 | ISC | https://github.com/npm/validate-npm-package-name |
| vary@1.1.2 | MIT | https://github.com/jshttp/vary |
| vdirs@0.1.8 | MIT |  |
| vooks@0.2.12 | MIT |  |
| vue-demi@0.14.10 | MIT | https://github.com/antfu/vue-demi |
| vue-eslint-parser@10.4.0 | MIT | https://github.com/vuejs/vue-eslint-parser |
| vue-i18n@11.4.0 | MIT | https://github.com/intlify/vue-i18n |
| vue-metamorph@3.3.4 | MIT | https://github.com/UnrefinedBrain/vue-metamorph |
| vue-router@4.6.4 | MIT | https://github.com/vuejs/router |
| vue-stick-to-bottom@1.0.0 | MIT | https://github.com/cwandev/vue-stick-to-bottom |
| vue-stream-markdown@0.7.2 | MIT | https://github.com/jinghaihan/vue-stream-markdown |
| vue@3.5.27 | MIT | https://github.com/vuejs/core |
| vueuc@0.4.65 | MIT |  |
| web-worker@1.5.0 | Apache-2.0 | https://github.com/developit/web-worker |
| which@2.0.2 | ISC | https://github.com/isaacs/node-which |
| which@4.0.0 | ISC | https://github.com/npm/node-which |
| word-wrap@1.2.5 | MIT | https://github.com/jonschlinkert/word-wrap |
| wrappy@1.0.2 | ISC | https://github.com/npm/wrappy |
| wsl-utils@0.1.0 | MIT | https://github.com/sindresorhus/wsl-utils |
| yallist@3.1.1 | ISC | https://github.com/isaacs/yallist |
| yocto-queue@0.1.0 | MIT | https://github.com/sindresorhus/yocto-queue |
| yocto-spinner@1.2.0 | MIT | https://github.com/sindresorhus/yocto-spinner |
| yoctocolors@2.1.2 | MIT | https://github.com/sindresorhus/yoctocolors |
| zod-to-json-schema@3.25.2 | ISC | https://github.com/StefanTerdell/zod-to-json-schema |
| zod@3.25.76 | MIT | https://github.com/colinhacks/zod |
| zod@4.4.3 | MIT | https://github.com/colinhacks/zod |
| zwitch@2.0.4 | MIT | https://github.com/wooorm/zwitch |

## Embedding model (runtime download)

On first semantic match, Prof-Finder may download an embedding model from ModelScope/Hugging Face:

| Component | License | Source |
|-----------|---------|--------|
| Qwen/Qwen3-Embedding-0.6B | Apache License 2.0 | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B |

Model weights are stored under the user-chosen data directory (`models/`). They are **not** committed to this repository.

## External services and data

These are accessed at runtime under your own account or network; terms are governed by each provider:

| Service | Use in Prof-Finder |
|---------|-------------------|
| [DeepSeek API](https://platform.deepseek.com) | LLM features (resume parsing, profiles, letters, chat) — user-supplied API key |
| [arXiv API](https://arxiv.org/help/api) | Paper metadata for source inputs |
| [Google Scholar](https://scholar.google.com) / [DBLP](https://dblp.org) | Professor and publication metadata (public web/API) |
| [ModelScope](https://www.modelscope.cn) | Optional model download mirror |

