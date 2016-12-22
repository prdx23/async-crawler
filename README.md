# Async Recursive Crawler

This is a simple crawler that crawls wikipidea starting from the given url, and crawls till the max depth given. It uses the new async/await coroutines introduced in [PEP 492](https://www.python.org/dev/peps/pep-0492/). 

### Running the script

Firstly install dependencies - 
```zsh
pip install aiohttp lxml
```
then you can call the script with different parameters, as defined in -
```zsh
python3 scraper.py --help
```

### Stats
These tests were run on a free tier [AWS EC2](https://aws.amazon.com/ec2/) server
<br>Current results :
```zsh
$ >> python3 scraper.py -d 1 -f graph-sm.json -w 20
Time Taken for 494 requests : 5.746156081557274 sec

$ >> python3 scraper.py -d 2 -f graph-md.json -w 20    
Time Taken for 36318 requests : 389.2725637294352 sec
```
The two json files created in above test are present in [data.tar.gz](https://github.com/Arsh23/async-crawler/blob/master/data.tar.gz) and are open-source. Feel free to use them anywhere.

The data in json is stored in the form of [Adjacency list](https://en.wikipedia.org/wiki/Adjacency_list), and all strings can be appended to `https://en.wikipedia.org/wiki/` to get the full url.
<br>Example json- 
```
{
  link1 : [list_of_adjecent_links_to_link1],
  link2 : [list_of_adjecent_links_to_link2],
  .
  .
}
```
