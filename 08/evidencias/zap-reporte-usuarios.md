# ZAP Scanning Report

ZAP by [Checkmarx](https://checkmarx.com/).


## Summary of Alerts

| Risk Level | Number of Alerts |
| --- | --- |
| High | 0 |
| Medium | 0 |
| Low | 1 |
| Informational | 2 |




## Insights

| Level | Reason | Site | Description | Statistic |
| --- | --- | --- | --- | --- |
| Low | Warning |  | ZAP warnings logged - see the zap.log file for details | 5    |
| Info | Informational |  | Percentage of network failures | 1 % |
| Info | Informational | http://localhost:5000 | Percentage of responses with status code 2xx | 7 % |
| Info | Informational | http://localhost:5000 | Percentage of responses with status code 4xx | 92 % |
| Info | Informational | http://localhost:5000 | Percentage of endpoints with content type application/json | 100 % |
| Info | Informational | http://localhost:5000 | Percentage of endpoints with method GET | 100 % |
| Info | Informational | http://localhost:5000 | Count of total endpoints | 4    |







## Alerts

| Name | Risk Level | Number of Instances |
| --- | --- | --- |
| Server Leaks Version Information via "Server" HTTP Response Header Field | Low | 4 |
| CORS Header | Informational | 1 |
| Non-Storable Content | Informational | 4 |




## Alert Detail



### [ Server Leaks Version Information via "Server" HTTP Response Header Field ](https://www.zaproxy.org/docs/alerts/10036/)



##### Low (High)

### Description

The web/application server is leaking version information via the "Server" HTTP response header. Access to such information may facilitate attackers identifying other vulnerabilities your web/application server is subject to.

* URL: http://localhost:5000/
  * Node Name: `http://localhost:5000/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Werkzeug/3.1.8 Python/3.12.3`
  * Other Info: ``
* URL: http://localhost:5000/robots.txt
  * Node Name: `http://localhost:5000/robots.txt`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Werkzeug/3.1.8 Python/3.12.3`
  * Other Info: ``
* URL: http://localhost:5000/sitemap.xml
  * Node Name: `http://localhost:5000/sitemap.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Werkzeug/3.1.8 Python/3.12.3`
  * Other Info: ``
* URL: http://localhost:5000/usuarios%3Fid=1
  * Node Name: `http://localhost:5000/usuarios (id)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Werkzeug/3.1.8 Python/3.12.3`
  * Other Info: ``


Instances: 4

### Solution

Ensure that your web server, application server, load balancer, etc. is configured to suppress the "Server" header or provide generic details.

### Reference


* [ https://httpd.apache.org/docs/current/mod/core.html#servertokens ](https://httpd.apache.org/docs/current/mod/core.html#servertokens)
* [ https://learn.microsoft.com/en-us/previous-versions/msp-n-p/ff648552(v=pandp.10) ](https://learn.microsoft.com/en-us/previous-versions/msp-n-p/ff648552(v=pandp.10))
* [ https://www.troyhunt.com/shhh-dont-let-your-response-headers/ ](https://www.troyhunt.com/shhh-dont-let-your-response-headers/)


#### CWE Id: [ 497 ](https://cwe.mitre.org/data/definitions/497.html)


#### WASC Id: 13

#### Source ID: 3

### [ CORS Header ](https://www.zaproxy.org/docs/alerts/40040/)



##### Informational (High)

### Description

Cross-Origin Resource Sharing (CORS) is an HTTP-header based mechanism that allows a server to indicate any other origins (domain, scheme, or port) than its own from which a browser should permit loading of resources. It relaxes the Same-Origin Policy (SOP).

* URL: http://localhost:5000/usuarios%3Fid=1
  * Node Name: `http://localhost:5000/usuarios (id)`
  * Method: `GET`
  * Parameter: ``
  * Attack: `origin: null`
  * Evidence: ``
  * Other Info: ``


Instances: 1

### Solution

If a web resource contains sensitive information, the origin should be properly specified in the Access-Control-Allow-Origin header. Only trusted websites needing this resource should be specified in this header, with the most secured protocol supported.

### Reference


* [ https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS ](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)
* [ https://portswigger.net/web-security/cors ](https://portswigger.net/web-security/cors)


#### CWE Id: [ 942 ](https://cwe.mitre.org/data/definitions/942.html)


#### WASC Id: 14

#### Source ID: 1

### [ Non-Storable Content ](https://www.zaproxy.org/docs/alerts/10049/)



##### Informational (Medium)

### Description

The response contents are not storable by caching components such as proxy servers. If the response does not contain sensitive, personal or user-specific information, it may benefit from being stored and cached, to improve performance.

* URL: http://localhost:5000/
  * Node Name: `http://localhost:5000/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `authorization:`
  * Other Info: ``
* URL: http://localhost:5000/robots.txt
  * Node Name: `http://localhost:5000/robots.txt`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `authorization:`
  * Other Info: ``
* URL: http://localhost:5000/sitemap.xml
  * Node Name: `http://localhost:5000/sitemap.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `authorization:`
  * Other Info: ``
* URL: http://localhost:5000/usuarios%3Fid=1
  * Node Name: `http://localhost:5000/usuarios (id)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `authorization:`
  * Other Info: ``


Instances: 4

### Solution

The content may be marked as storable by ensuring that the following conditions are satisfied:
The request method must be understood by the cache and defined as being cacheable ("GET", "HEAD", and "POST" are currently defined as cacheable)
The response status code must be understood by the cache (one of the 1XX, 2XX, 3XX, 4XX, or 5XX response classes are generally understood)
The "no-store" cache directive must not appear in the request or response header fields
For caching by "shared" caches such as "proxy" caches, the "private" response directive must not appear in the response
For caching by "shared" caches such as "proxy" caches, the "Authorization" header field must not appear in the request, unless the response explicitly allows it (using one of the "must-revalidate", "public", or "s-maxage" Cache-Control response directives)
In addition to the conditions above, at least one of the following conditions must also be satisfied by the response:
It must contain an "Expires" header field
It must contain a "max-age" response directive
For "shared" caches such as "proxy" caches, it must contain a "s-maxage" response directive
It must contain a "Cache Control Extension" that allows it to be cached
It must have a status code that is defined as cacheable by default (200, 203, 204, 206, 300, 301, 404, 405, 410, 414, 501).

### Reference


* [ https://datatracker.ietf.org/doc/html/rfc7234 ](https://datatracker.ietf.org/doc/html/rfc7234)
* [ https://datatracker.ietf.org/doc/html/rfc7231 ](https://datatracker.ietf.org/doc/html/rfc7231)
* [ https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html ](https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html)


#### CWE Id: [ 524 ](https://cwe.mitre.org/data/definitions/524.html)


#### WASC Id: 13

#### Source ID: 3


