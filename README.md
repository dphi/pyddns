pyddns
======

pyddns is a cgi script that allows updates to dns records using
HTTP Get requests. It only has python dependencies, i.e. "nsupdate"
is not being used.

Inspired by 
 * Matthias Kadenbach's php-dynamic-dns-server 
   * The HTTP Get interface is from there
   * https://github.com/mattes/php-dynamic-dns-server

 * Matt Ryanczak's pure python dnsupdate.py script 
   * dnsupdate.py is being used to update dns records
   * http://planetfoo.org/blog/archive/2012/01/24/a-better-nsupdate/
   * http://planetfoo.org/files/dnsupdate.py


If you see error messages like "TypeError: unsupported operand type(s) for &: 'str' and 'long'" you may need to update your version of dnspython. Debian users may also track http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=593939.


Licence
=======
Released under the MIT license
http://opensource.org/licenses/MIT
