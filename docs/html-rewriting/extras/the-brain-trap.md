# Problem features that make HTML rewriting cognitively complex

## Overview

I believe there are features of this issue that raise the difficulty of 
thinking about it above and beyond the inherant complexity.

The problem is difficult, but this mostly causes problems with skill or 
knowledge: that is not what this page is attempting to discuss.

This page attempts to identify qualities that effect _judgement_ which can
effect the reliability of our assessment and the quality of our planning 
regardless of skill.

## Effort-to-features does not obey usual patterns

We are all used to the 80/20 rule which is the idea that you get 80% of the 
features for 20% of the effort. This is often then case and applies here as well.

The cognitive pitfall is that:

 * Usually you get 80% of the features 100% of the time
 * Here you get **100% of the features 80% of the time and 0% the rest**
 
We are not used to thinking in these terms, and it makes planning difficult.

We often discussed "getting to the point where pages are good enough". This 
MVP idea is rooted in the concept of a general level of quality which is 
increased uniformly with effort.

HTML rewriting does not work this way, and it takes effort to let go of 
traditional planning techniques.  

## The system in play is much larger than usual

In the most congnitively friendly situations we can place an abstraction around
a particular item and consider it in isolation (e.g. unit testing).

When we cast the net wider, we might consider the "system" we are creating to
include the database, or webserver as well as the app we are creating.

In this case the relevant "system" in play contains:

 * Our code
 * Our infrastructure
 * The browser
 * The source website and it's infrastucture
 * The entire web connecting the above
 * Interactions between all of the above

This is often _true_, but it's less often _relevant_ and we aren't really used
to thinking about it all at once.

### It's in the complex / chaotic domain

This work is certainly in the complex domain, which is defined by a system 
where our actions change the system we are interacting with. For example when
streaming from a website, that site might change it's behavior because we are
streaming.

On occasions the complexity and network connectivity combine to verge
on the chaotic domain, where cause and effect are not clear at all. Things
"just happen".

This is an inherently uncomfortable place to be, as we eventually end up trying
things and random to see what helps.

### This can lead to unsatisfying conclusions

I cannot tell you if the Project Gutenburg site works on our solution or not. 
It failed yesterday, and worked the day before. I don't think anything on our 
end changed.

At it's core, whether Project Gutenburg works on our solution may not just be
unknown, _it may be unknowable_.

This doesn't make for good reading, and so we tend to shy away from it.

## High initial return on effort promotes over-confidence

A number of combining factors of engineers and this particular problem combine
to make it hard to trust our judgements:

### Engineers are a positive lot
 
Engineers tend to be, and are often required to be, over confident when 
approaching issues. A strong (if inaccurate) feeling that a solution can be 
found is a useful foundation to provide the necessary willpower to find it.

After the fact if no solution is found it is forgotten, but if one is found
the original assessment is judged as accurate. In fact we may have had no idea
at all, and sheer dogged determination might have served just as well.

### We are most confident when we are ignorant of our ignorance

Junior developers, or experienced developers moving into a new domain are often
unaware of how little they know about it. This [robs them of the required tools
to assess their own skill⬈](https://en.wikipedia.org/wiki/Dunning%E2%80%93Kruger_effect).

### This problem has nasty features that combine with the above

The previous two observations are general truisms about cognative bias, but 
HTML rewriting has some nasty features which work to bring those out:

 * Initial phases require little knowledge and yield impressive results quickly
 * Additional results after that require iteratively more knowledge and effort
  for less reward
 * Solving the problem forces you to continually move into new and potentially
  unfamiliar problem domains (NGINX, to HTML parsing, to HTML standards, 
  to cookies, to cookie security standards...)
  
At each stage a person is likely to:

 * Feel a rush of validation that the problem can be solved
 * Believe their initial assessment that it can be done
 * Over estimate the percentage that is solved at this point
 * Under estimate the amount of the issue they don't yet understand in the 
   new domain
 * Not foresee the next domain shift required
 
This leads to a constant feeling that you have "nearly" finished. 

I have this feeling. I think we are nearly done but for a little more effort. 
I have thought that many times during this work. I don't believe I should
be trusted.

# Summary

This problem:

 * Has an initial high reward
 * Progressively provides less reward requiring more effort
 * Provides reward inconsistently and randomly (chaotic domain)

These are all features of systems designed to capture and foster long term
compulsive behaviors. If you are wondering why many developers have had a go at
this and got sucked in, this may be why. 

In addition it has features which cause our normal ways of planning and 
assessing progress difficult, misleading or logically impossible.

For these reasons I suggest we:

## Be skeptical of developer assessments of progress

Fairly self explanatory, but we should be aware are assessments or progress 
and estimates of remaining work are likely to be unreliable.

## Seek external measures of progress separated from implementers

Many of the biases above predominanly effect people involved in development of
the product. For that reason non-technical may be in a better place to 
dispassionately assess if we are on track.

A list of concrete measures might also help.

## Frame discussions in ways that accept the chaotic nature of the product

> "Works on 95% of websites"

Has a very different feel to

> "Worked on 95% of the 100 websites as we were checking them, but by now 
> who knows"

The first sounds better, and makes a nicer report. The second one is more 
accurate, and makes for better planning.

## Seek less chaotic solutions 

A problem which is easier to think about doesn't just increase the chance we 
can solve it. It also increases the change we can be sure we have.