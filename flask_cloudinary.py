from cloudinary import uploader #pip install git+https://github.com/cloudinary/pycloudinary/

class Cloudinary(object):
  def __init__(self, app):
    config = app.config['CLOUDINARY_URL'].split('://')[1]
    config = config.replace("@", ":")
    self.api_key, self.api_secret, self.name = config.split(":")

  def upload(self, image):
    res = uploader.call_api(
      "upload",
      uploader.build_upload_params(),
      api_key=self.api_key,
      api_secret=self.api_secret,
      cloud_name=self.name,
      file=image.stream,
    )
    return res

    ''' res example:
    {
      u'secure_url': u'https://d3jpl91pxevbkh.cloudfront.net/huouwlpzr/image/upload/v1358978552/1001.png', 
      u'public_id': u'1001', 
      u'format': u'png', 
      u'url': u'http://res.cloudinary.com/huouwlpzr/image/upload/v1358978552/1001.png', 
      u'bytes': 4487, 
      u'height': 512, 
      u'width': 512, 
      u'version': 1358978552, 
      u'signature': u'6064602083ccb2fa86d73f979d8c70ea4bff731d', 
      u'resource_type': u'image'
    }
    '''