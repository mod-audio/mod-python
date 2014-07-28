pkgname=mod-common
pkgver=0.99.3
pkgrel=1
pkgdesc="MOD Libraries"
license=("BSD")
depends=('python2' 'python2-rdflib' 'python-whoosh' 'python2-pymongo')
makedepends=('python2-distribute')
arch=('any')

package() {
  cd ${startdir}
  python2 setup.py install --root="${pkgdir}"
}
