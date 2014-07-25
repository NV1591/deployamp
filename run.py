#!flask/bin/python

from app import app
app.run(debug=True)

# #!flask/bin/python
# from app import app
# import os
# port = int(os.environ.get('PORT', 3000))
# app.run(host='0.0.0.0', port=port)
