# Learnings

## img srcsets + img data-src

Gotta parse them (srcsets only) and make them absolute

## css

Need to proxy it so relative images work

Absolute URLs starting from / in external files are bust

# Youtube messes with the path

It eliminates everything after the domain and genrally messes about with it

# New-yorker has badly encoded stuff

http://localhost:9082/html?url=https%3A%2F%2Fwww.newyorker.com%2Fbooks%2Fpage-turner%2Fcity-of-women

Not sure what's going on here but lots of HTML entities coming out

# UnicodeDammit is _slow_

Like 10 seconds vs 50ms to parse slow. This is a shame, because we don't really
have a way of dealing with badly encoded pages. (Or any real handling right now)

# Do we have to proxy cookies?

Some GDPR popups and things really don't work (you can never dismiss them) as 
they store the answer in cookies. Perhaps we have to proxy the cookies through?