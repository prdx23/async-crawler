# Async Recursive Crawler

This is a simple crawler that crawls webpages according to the regex provided, starting from the given url, and crawls till the max depth given. It uses the new async/await coroutines introduced in [PEP 492](https://www.python.org/dev/peps/pep-0492/). 

### Todo
- create a network visualization with the data saved
- convert mongodb operations to bulk update

### Stats
These tests were run on a free tier [AWS EC2](https://aws.amazon.com/ec2/) server with [this starting url](https://en.wikipedia.org/wiki/Python_(programming_language)).
<br>Current results :

- Time Taken for 494 requests(recursion level 1) : 5.484668092802167 sec
- Time Taken for 36997 requests(recursion level 2) : 415.45510824956 sec

### Dependencies

- [python 3.6](https://www.python.org/downloads/release/python-360/)
- [lxml](http://lxml.de/)
- [aiohttp](http://aiohttp.readthedocs.io/en/stable/)
- [motor](https://motor.readthedocs.io/en/stable/)
