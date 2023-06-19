from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config


@view_config(route_name="api.youtube.transcript", permission="api", renderer="json")
def transcript(request):
    """Return the transcript of a given YouTube video."""

    video_id = request.matchdict["video_id"]

    if video_id != "1":
        raise HTTPNotFound()

    # pylint:disable=too-many-lines
    return {
        "data": {
            "type": "transcripts",
            "id": video_id,
            "attributes": {
                "segments": [
                    {
                        "text": "[Music]",
                        "start": 0.0,
                    },
                    {
                        "text": "how many of you remember the first time",
                        "start": 5.6,
                    },
                    {
                        "text": "you saw a playstation 1 game if you were",
                        "start": 7.52,
                    },
                    {
                        "text": "a part of the era when the console was",
                        "start": 10.32,
                    },
                    {
                        "text": "released your jaw probably hit the floor",
                        "start": 12.24,
                    },
                    {
                        "text": "when you first saw a ridge racer or",
                        "start": 15.12,
                    },
                    {
                        "text": "tekken 2. these were very faithful",
                        "start": 16.88,
                    },
                    {
                        "text": "arcade ports that sony brought to the",
                        "start": 19.359,
                    },
                    {
                        "text": "living rooms and bedrooms of gamers all",
                        "start": 21.6,
                    },
                    {
                        "text": "around the world if you experienced the",
                        "start": 23.76,
                    },
                    {
                        "text": "system later on or indeed in recent",
                        "start": 26.4,
                    },
                    {
                        "text": "times with the playstation classic you",
                        "start": 28.72,
                    },
                    {
                        "text": "may be left wondering what was all the",
                        "start": 31.039,
                    },
                    {
                        "text": "fuss about the playstation hardware was",
                        "start": 32.96,
                    },
                    {
                        "text": "built from the ground up as a dedicated",
                        "start": 35.6,
                    },
                    {
                        "text": "games machine and crucial to the",
                        "start": 37.6,
                    },
                    {
                        "text": "architecture would be its 3d",
                        "start": 39.52,
                    },
                    {
                        "text": "capabilities and those capabilities were",
                        "start": 41.52,
                    },
                    {
                        "text": "extremely fast with the system capable",
                        "start": 44.079,
                    },
                    {
                        "text": "of pushing many thousands of polygons",
                        "start": 46.64,
                    },
                    {
                        "text": "around the screen any given second but",
                        "start": 48.559,
                    },
                    {
                        "text": "if you compare the playstation with the",
                        "start": 50.879,
                    },
                    {
                        "text": "3d of its biggest rival the nintendo 64",
                        "start": 52.64,
                    },
                    {
                        "text": "the graphics can look quite primitive",
                        "start": 55.92,
                    },
                    {
                        "text": "even worse is the shimmering wobbling",
                        "start": 58.079,
                    },
                    {
                        "text": "and popping in and out of textures as",
                        "start": 60.96,
                    },
                    {
                        "text": "the camera is moved around",
                        "start": 62.879,
                    },
                    {
                        "text": "this is notable in something like metal",
                        "start": 64.799,
                    },
                    {
                        "text": "gear solid these effects or side effects",
                        "start": 66.88,
                    },
                    {
                        "text": "i should say is a part of what gave the",
                        "start": 69.92,
                    },
                    {
                        "text": "playstation 1 its charm but what",
                        "start": 71.76,
                    },
                    {
                        "text": "actually is going on here and why does",
                        "start": 74.4,
                    },
                    {
                        "text": "the nintendo 64 exhibit no such issues",
                        "start": 76.88,
                    },
                    {
                        "text": "yet the playstation 1 seems to have this",
                        "start": 79.92,
                    },
                    {
                        "text": "problem on every single game the",
                        "start": 82.72,
                    },
                    {
                        "text": "playstation 1 does excellent 3d and it",
                        "start": 84.64,
                    },
                    {
                        "text": "was an absolute powerhouse when it came",
                        "start": 88.24,
                    },
                    {
                        "text": "out pushing many polygons per second",
                        "start": 90.24,
                    },
                    {
                        "text": "extremely fast but the playstation 1 has",
                        "start": 93.04,
                    },
                    {
                        "text": "a unique and interesting look about it",
                        "start": 95.84,
                    },
                    {
                        "text": "that is very easy to pick out in a crowd",
                        "start": 98.24,
                    },
                    {
                        "text": "that you could just say that looks like",
                        "start": 100.64,
                    },
                    {
                        "text": "a playstation one game to me and you",
                        "start": 102.399,
                    },
                    {
                        "text": "would probably be right",
                        "start": 104.399,
                    },
                    {
                        "text": "to explain this we need to take a closer",
                        "start": 106.479,
                    },
                    {
                        "text": "look at the architecture of the",
                        "start": 108.56,
                    },
                    {
                        "text": "playstation 1. at the heart of the",
                        "start": 110.0,
                    },
                    {
                        "text": "system is the mips r3000a cpu it's a",
                        "start": 112.24,
                    },
                    {
                        "text": "32-bit processor running at 33 megahertz",
                        "start": 116.079,
                    },
                    {
                        "text": "as with almost every cpu out there it",
                        "start": 119.36,
                    },
                    {
                        "text": "has an alu or arithmetic logic unit",
                        "start": 121.68,
                    },
                    {
                        "text": "what's missing however is an fpu or",
                        "start": 124.32,
                    },
                    {
                        "text": "floating point unit this is important",
                        "start": 126.64,
                    },
                    {
                        "text": "and we'll come back to this later on",
                        "start": 129.039,
                    },
                    {
                        "text": "the ps1 has two co-processors cop0 and",
                        "start": 131.28,
                    },
                    {
                        "text": "cop2 cop2 is for the gpu and that's the",
                        "start": 134.64,
                    },
                    {
                        "text": "one that we are interested in the gpu is",
                        "start": 138.16,
                    },
                    {
                        "text": "responsible of course for the graphical",
                        "start": 141.04,
                    },
                    {
                        "text": "output the ps1 has a one megabyte frame",
                        "start": 142.8,
                    },
                    {
                        "text": "buffer at a maximum of 1024",
                        "start": 145.92,
                    },
                    {
                        "text": "by 512 pixels there's also a 2 kilobyte",
                        "start": 148.72,
                    },
                    {
                        "text": "texture cache for speed also interesting",
                        "start": 152.0,
                    },
                    {
                        "text": "is that the gpus frame buffer is not",
                        "start": 154.48,
                    },
                    {
                        "text": "directly accessible from the cpu at all",
                        "start": 156.4,
                    },
                    {
                        "text": "in other words you can't directly draw",
                        "start": 158.72,
                    },
                    {
                        "text": "into it rather commands are sent to the",
                        "start": 160.4,
                    },
                    {
                        "text": "cpu to place objects into the frame",
                        "start": 162.72,
                    },
                    {
                        "text": "buffer this is done with what's known as",
                        "start": 165.04,
                    },
                    {
                        "text": "ordering tables these tables tell the",
                        "start": 167.2,
                    },
                    {
                        "text": "gpu how and where to draw each primitive",
                        "start": 169.599,
                    },
                    {
                        "text": "and they are then sent to the gpu in the",
                        "start": 172.4,
                    },
                    {
                        "text": "order that you wish to draw the 3d scene",
                        "start": 174.48,
                    },
                    {
                        "text": "the gpu can draw triangles rectangles",
                        "start": 176.8,
                    },
                    {
                        "text": "lines points and sprites textures can",
                        "start": 179.76,
                    },
                    {
                        "text": "also be applied to polygons and sprites",
                        "start": 182.48,
                    },
                    {
                        "text": "there's also different color modes and",
                        "start": 185.04,
                    },
                    {
                        "text": "this is all pretty standard stuff for a",
                        "start": 187.04,
                    },
                    {
                        "text": "90s 3d gpu but what's interesting about",
                        "start": 188.8,
                    },
                    {
                        "text": "the ps1 is that there is another custom",
                        "start": 191.519,
                    },
                    {
                        "text": "chip that is the heart of all 3d",
                        "start": 194.159,
                    },
                    {
                        "text": "calculations that is known as the gte or",
                        "start": 196.159,
                    },
                    {
                        "text": "geometry transformation engine this",
                        "start": 198.879,
                    },
                    {
                        "text": "engine is used for fast vector",
                        "start": 201.2,
                    },
                    {
                        "text": "mathematics to handle rotation",
                        "start": 202.72,
                    },
                    {
                        "text": "translation perspective and more of",
                        "start": 204.48,
                    },
                    {
                        "text": "course a cpu can handle this for you but",
                        "start": 206.959,
                    },
                    {
                        "text": "even with the most optimized code this",
                        "start": 209.519,
                    },
                    {
                        "text": "is the main job of the gte and will",
                        "start": 211.76,
                    },
                    {
                        "text": "perform these operations much faster in",
                        "start": 214.0,
                    },
                    {
                        "text": "fact the gte can manage on average 360",
                        "start": 216.48,
                    },
                    {
                        "text": "000 flat shaded polygons per second",
                        "start": 220.239,
                    },
                    {
                        "text": "the playstation 1 has three main",
                        "start": 223.28,
                    },
                    {
                        "text": "limitations when it comes to graphics no",
                        "start": 224.959,
                    },
                    {
                        "text": "mit mapping no z buffer and no floating",
                        "start": 227.2,
                    },
                    {
                        "text": "point numbers let's take a look at each",
                        "start": 229.76,
                    },
                    {
                        "text": "of these mit mapping is a technique",
                        "start": 231.519,
                    },
                    {
                        "text": "where a single texture is scaled and",
                        "start": 233.439,
                    },
                    {
                        "text": "filtered at different resolutions these",
                        "start": 235.36,
                    },
                    {
                        "text": "are pre-calculated sequences that help",
                        "start": 237.2,
                    },
                    {
                        "text": "eliminate alias effects and also",
                        "start": 239.04,
                    },
                    {
                        "text": "increase performance because these",
                        "start": 241.04,
                    },
                    {
                        "text": "mipmaps are generally cached the",
                        "start": 242.879,
                    },
                    {
                        "text": "downside of mipmapping is textures at",
                        "start": 245.04,
                    },
                    {
                        "text": "low resolutions appear blurrier the",
                        "start": 247.2,
                    },
                    {
                        "text": "nintendo 64 has mipmapping enabled for",
                        "start": 249.28,
                    },
                    {
                        "text": "example in these scenes in perfect dark",
                        "start": 251.68,
                    },
                    {
                        "text": "but sometimes the nintendo 64 gets",
                        "start": 254.0,
                    },
                    {
                        "text": "criticized for appearing too blurry and",
                        "start": 256.0,
                    },
                    {
                        "text": "this is one of the reasons why on the",
                        "start": 258.239,
                    },
                    {
                        "text": "flip side on a standard crt even with a",
                        "start": 260.4,
                    },
                    {
                        "text": "composite signal the playstation 1 could",
                        "start": 262.88,
                    },
                    {
                        "text": "look very good with a very crisp and",
                        "start": 264.96,
                    },
                    {
                        "text": "nice looking signal",
                        "start": 266.96,
                    },
                    {
                        "text": "the downside of course is that on a",
                        "start": 268.4,
                    },
                    {
                        "text": "modern hdtv a ps1 3d game does not look",
                        "start": 270.16,
                    },
                    {
                        "text": "very good it looks very pixelated and",
                        "start": 273.759,
                    },
                    {
                        "text": "upscaling and other things don't always",
                        "start": 276.16,
                    },
                    {
                        "text": "help",
                        "start": 278.16,
                    },
                    {
                        "text": "but lack of mint mapping isn't the",
                        "start": 279.6,
                    },
                    {
                        "text": "reason why textures warp around there",
                        "start": 281.199,
                    },
                    {
                        "text": "are still some things to cover a zed or",
                        "start": 283.28,
                    },
                    {
                        "text": "z buffer is an important part of any 3d",
                        "start": 286.0,
                    },
                    {
                        "text": "graphics hardware and it was left out of",
                        "start": 288.479,
                    },
                    {
                        "text": "the playstation 1. to best explain a z",
                        "start": 290.56,
                    },
                    {
                        "text": "buffer think of a painting or a drawing",
                        "start": 293.36,
                    },
                    {
                        "text": "an artist is attempting to recreate a 3d",
                        "start": 295.919,
                    },
                    {
                        "text": "scene on a 2d plane like a canvas or a",
                        "start": 298.479,
                    },
                    {
                        "text": "piece of paper typically the sky horizon",
                        "start": 301.28,
                    },
                    {
                        "text": "and background objects in the distance",
                        "start": 304.24,
                    },
                    {
                        "text": "are drawn first followed by closer",
                        "start": 306.0,
                    },
                    {
                        "text": "objects and then followed by the closest",
                        "start": 308.08,
                    },
                    {
                        "text": "ones that way the illusion of",
                        "start": 310.24,
                    },
                    {
                        "text": "perspective is maintained but in order",
                        "start": 312.0,
                    },
                    {
                        "text": "to make things look realistic the hidden",
                        "start": 314.32,
                    },
                    {
                        "text": "surfaces must not be filled in in a 3d",
                        "start": 316.16,
                    },
                    {
                        "text": "world we have x and y coordinates to",
                        "start": 318.8,
                    },
                    {
                        "text": "determine placement but the z or z",
                        "start": 320.72,
                    },
                    {
                        "text": "coordinate is used for depth or in other",
                        "start": 323.039,
                    },
                    {
                        "text": "words how far from the camera the object",
                        "start": 325.28,
                    },
                    {
                        "text": "is being placed the z buffer manages the",
                        "start": 327.199,
                    },
                    {
                        "text": "depth of every single object in the",
                        "start": 329.84,
                    },
                    {
                        "text": "scene and essentially solves this hidden",
                        "start": 331.68,
                    },
                    {
                        "text": "surface problem for you",
                        "start": 333.84,
                    },
                    {
                        "text": "on the playstation the gpu lacks a z",
                        "start": 336.56,
                    },
                    {
                        "text": "buffer so no depth or z information is",
                        "start": 339.199,
                    },
                    {
                        "text": "ever passed to the gpu and there is no",
                        "start": 341.68,
                    },
                    {
                        "text": "way in hardware to do proper hidden",
                        "start": 343.919,
                    },
                    {
                        "text": "surface removal as an example of lack of",
                        "start": 346.0,
                    },
                    {
                        "text": "z buffer let's consider the original",
                        "start": 348.88,
                    },
                    {
                        "text": "tech demo the t-rex that stunned",
                        "start": 350.96,
                    },
                    {
                        "text": "developers with the power of the",
                        "start": 352.96,
                    },
                    {
                        "text": "playstation if we take a closer look at",
                        "start": 354.32,
                    },
                    {
                        "text": "the animation of the t-rex everything is",
                        "start": 356.479,
                    },
                    {
                        "text": "rendering correctly with the triangles",
                        "start": 358.72,
                    },
                    {
                        "text": "furthest away from the camera hidden by",
                        "start": 360.479,
                    },
                    {
                        "text": "the body of the t-rex that's closer to",
                        "start": 362.96,
                    },
                    {
                        "text": "the camera so we just said that the",
                        "start": 365.199,
                    },
                    {
                        "text": "playstation has no z buffer in hardware",
                        "start": 367.039,
                    },
                    {
                        "text": "so how is this possible well it doesn't",
                        "start": 369.12,
                    },
                    {
                        "text": "mean that one can't be built in software",
                        "start": 371.199,
                    },
                    {
                        "text": "and that's one of the complexities for",
                        "start": 373.84,
                    },
                    {
                        "text": "the developer essentially triangles need",
                        "start": 375.52,
                    },
                    {
                        "text": "to be sent to the playstation gpu in",
                        "start": 378.24,
                    },
                    {
                        "text": "order of depth with the ones furthest",
                        "start": 380.72,
                    },
                    {
                        "text": "away being sent first all the way to the",
                        "start": 382.72,
                    },
                    {
                        "text": "nearest ones the hardware will still",
                        "start": 384.96,
                    },
                    {
                        "text": "render it for you and hide polygons that",
                        "start": 386.96,
                    },
                    {
                        "text": "are furthest away",
                        "start": 388.8,
                    },
                    {
                        "text": "so what exactly is the problem here and",
                        "start": 390.319,
                    },
                    {
                        "text": "why can't the developer just sort the",
                        "start": 392.88,
                    },
                    {
                        "text": "triangles in correct order and pass them",
                        "start": 394.479,
                    },
                    {
                        "text": "to the gpu well that's exactly what most",
                        "start": 396.4,
                    },
                    {
                        "text": "developers did when they develop games",
                        "start": 398.8,
                    },
                    {
                        "text": "for the playstation the problem here is",
                        "start": 400.8,
                    },
                    {
                        "text": "is that textures need to be applied to",
                        "start": 402.8,
                    },
                    {
                        "text": "each polygon which rely on accurate",
                        "start": 404.56,
                    },
                    {
                        "text": "depth values because no depth values are",
                        "start": 406.8,
                    },
                    {
                        "text": "sent to the gpu textures are applied",
                        "start": 409.44,
                    },
                    {
                        "text": "with what's known as a fine texture",
                        "start": 411.52,
                    },
                    {
                        "text": "mapping the edges of the polygons are",
                        "start": 413.599,
                    },
                    {
                        "text": "correct but the textured scan lines",
                        "start": 415.52,
                    },
                    {
                        "text": "drawn between the edges to fill them",
                        "start": 417.68,
                    },
                    {
                        "text": "don't calculate perspective each texture",
                        "start": 419.599,
                    },
                    {
                        "text": "element or texel are the same size and",
                        "start": 422.24,
                    },
                    {
                        "text": "the result is this",
                        "start": 424.639,
                    },
                    {
                        "text": "a way to improve this was to break the",
                        "start": 426.639,
                    },
                    {
                        "text": "polygon up into smaller triangles but",
                        "start": 428.479,
                    },
                    {
                        "text": "this may mean lots of processing is done",
                        "start": 430.56,
                    },
                    {
                        "text": "on non-essential parts of the scene like",
                        "start": 432.479,
                    },
                    {
                        "text": "room models floors and ceilings with",
                        "start": 435.12,
                    },
                    {
                        "text": "less triangles generally in floor",
                        "start": 437.52,
                    },
                    {
                        "text": "textures like racing games they may",
                        "start": 439.12,
                    },
                    {
                        "text": "generally be larger in size and that's",
                        "start": 441.199,
                    },
                    {
                        "text": "why you see more warping in the floor on",
                        "start": 443.44,
                    },
                    {
                        "text": "many games",
                        "start": 445.52,
                    },
                    {
                        "text": "the nintendo 64 has proper perspective",
                        "start": 446.96,
                    },
                    {
                        "text": "calculation and a z buffer it also has",
                        "start": 449.68,
                    },
                    {
                        "text": "mint mapping and as you can see with the",
                        "start": 452.16,
                    },
                    {
                        "text": "comparison with mega man 64 and mega man",
                        "start": 453.84,
                    },
                    {
                        "text": "legends on the ps1 the wall textures on",
                        "start": 456.639,
                    },
                    {
                        "text": "the ps1 show signs of warping due to the",
                        "start": 459.28,
                    },
                    {
                        "text": "affine texture mapping on the nintendo",
                        "start": 462.16,
                    },
                    {
                        "text": "64 the perspective calculation is",
                        "start": 464.4,
                    },
                    {
                        "text": "accurate",
                        "start": 466.8,
                    },
                    {
                        "text": "there's also other issues due to the",
                        "start": 468.639,
                    },
                    {
                        "text": "lack of z buffer if we consider these",
                        "start": 470.4,
                    },
                    {
                        "text": "three rectangles and trying to render",
                        "start": 472.479,
                    },
                    {
                        "text": "them without a z buffer which rectangle",
                        "start": 474.24,
                    },
                    {
                        "text": "is closest to the camera and which ones",
                        "start": 476.479,
                    },
                    {
                        "text": "are hidden once again a solution may be",
                        "start": 478.56,
                    },
                    {
                        "text": "to break these rectangles into much",
                        "start": 480.879,
                    },
                    {
                        "text": "smaller triangles and hide them but this",
                        "start": 482.479,
                    },
                    {
                        "text": "comes at a cost it also is not entirely",
                        "start": 484.56,
                    },
                    {
                        "text": "accurate back to the t-rex demo as we",
                        "start": 487.039,
                    },
                    {
                        "text": "see the dinosaur walking you can see the",
                        "start": 489.599,
                    },
                    {
                        "text": "textures popping in and out at the hind",
                        "start": 491.759,
                    },
                    {
                        "text": "legs this is because of the lack of z",
                        "start": 493.68,
                    },
                    {
                        "text": "buffer it's left up to the programmer to",
                        "start": 495.68,
                    },
                    {
                        "text": "determine which triangle gets displayed",
                        "start": 497.68,
                    },
                    {
                        "text": "and which one does not",
                        "start": 499.759,
                    },
                    {
                        "text": "there's also the phenomenon where",
                        "start": 502.16,
                    },
                    {
                        "text": "polygons would jitter around for no",
                        "start": 503.84,
                    },
                    {
                        "text": "apparent reason this is another side",
                        "start": 505.759,
                    },
                    {
                        "text": "effect of the playstation 1 hardware",
                        "start": 507.759,
                    },
                    {
                        "text": "remember we mentioned earlier that the",
                        "start": 509.919,
                    },
                    {
                        "text": "playstation does not support floating",
                        "start": 511.44,
                    },
                    {
                        "text": "point values this is the root cause the",
                        "start": 513.36,
                    },
                    {
                        "text": "playstation uses fixed point integers",
                        "start": 516.08,
                    },
                    {
                        "text": "essentially this means that the vector",
                        "start": 518.56,
                    },
                    {
                        "text": "calculations that are needed to rotate",
                        "start": 520.08,
                    },
                    {
                        "text": "translate and calculate new values was",
                        "start": 522.88,
                    },
                    {
                        "text": "integer only the gte only of outputs",
                        "start": 525.36,
                    },
                    {
                        "text": "results as integer pixel coordinates",
                        "start": 528.24,
                    },
                    {
                        "text": "without any fractional portion the",
                        "start": 530.32,
                    },
                    {
                        "text": "playstation cannot display any sub pixel",
                        "start": 532.48,
                    },
                    {
                        "text": "movements and the polygons would just",
                        "start": 535.04,
                    },
                    {
                        "text": "snap into place until one of its",
                        "start": 536.88,
                    },
                    {
                        "text": "vertices moves enough to snap into a",
                        "start": 538.959,
                    },
                    {
                        "text": "different pixel this is the dreaded",
                        "start": 541.44,
                    },
                    {
                        "text": "wobble effect that you see on many games",
                        "start": 543.76,
                    },
                    {
                        "text": "and is a part of the fabric that makes",
                        "start": 545.839,
                    },
                    {
                        "text": "up the playstation 1. but as 3d hardware",
                        "start": 547.68,
                    },
                    {
                        "text": "is much more powerful these days",
                        "start": 550.56,
                    },
                    {
                        "text": "advances in playstation 1 emulators",
                        "start": 552.48,
                    },
                    {
                        "text": "means we are able to patch and fix these",
                        "start": 554.959,
                    },
                    {
                        "text": "issues with z buffer and sub pixel",
                        "start": 557.12,
                    },
                    {
                        "text": "movements to remove the warping and",
                        "start": 559.04,
                    },
                    {
                        "text": "wobble of polygons these are simple",
                        "start": 560.959,
                    },
                    {
                        "text": "emulation options that can be applied",
                        "start": 563.2,
                    },
                    {
                        "text": "and in many ways this makes the games",
                        "start": 565.36,
                    },
                    {
                        "text": "much different than how they used to be",
                        "start": 567.76,
                    },
                    {
                        "text": "it's fair to say that these issues would",
                        "start": 570.32,
                    },
                    {
                        "text": "have driven programmers mad having to",
                        "start": 572.08,
                    },
                    {
                        "text": "develop sorting algorithms determine the",
                        "start": 574.16,
                    },
                    {
                        "text": "number of triangles to use how to reduce",
                        "start": 576.32,
                    },
                    {
                        "text": "warping and wobble it wouldn't have been",
                        "start": 578.88,
                    },
                    {
                        "text": "fun but these days people seem to",
                        "start": 580.88,
                    },
                    {
                        "text": "embrace the playstation 1 graphical",
                        "start": 583.12,
                    },
                    {
                        "text": "style calling it retro and it's",
                        "start": 584.959,
                    },
                    {
                        "text": "something that you can download and use",
                        "start": 587.2,
                    },
                    {
                        "text": "shaders that accurately will reproduce",
                        "start": 589.12,
                    },
                    {
                        "text": "playstation 1 style effects on engines",
                        "start": 591.44,
                    },
                    {
                        "text": "like unity and i personally wouldn't",
                        "start": 593.519,
                    },
                    {
                        "text": "have it any other way the playstation 1",
                        "start": 595.68,
                    },
                    {
                        "text": "with its quirks the wobble the warping",
                        "start": 597.92,
                    },
                    {
                        "text": "all these issues remind me of the golden",
                        "start": 600.16,
                    },
                    {
                        "text": "age of video games in the mid to late",
                        "start": 602.24,
                    },
                    {
                        "text": "90s where games were starting to mature",
                        "start": 604.0,
                    },
                    {
                        "text": "arcades were becoming very popular and",
                        "start": 606.8,
                    },
                    {
                        "text": "3d on home consoles were just getting",
                        "start": 609.36,
                    },
                    {
                        "text": "started it's really hard to know",
                        "start": 611.68,
                    },
                    {
                        "text": "why sony omitted these features from the",
                        "start": 614.0,
                    },
                    {
                        "text": "graphics hardware on the sony",
                        "start": 616.56,
                    },
                    {
                        "text": "playstation i",
                        "start": 618.079,
                    },
                    {
                        "text": "think if i was to guess it's probably to",
                        "start": 619.68,
                    },
                    {
                        "text": "cut some costs on the retail price of",
                        "start": 623.12,
                    },
                    {
                        "text": "the system it wanted to be very",
                        "start": 626.24,
                    },
                    {
                        "text": "competitive with the sega satin and the",
                        "start": 628.32,
                    },
                    {
                        "text": "3do and obviously it completely",
                        "start": 630.56,
                    },
                    {
                        "text": "destroyed the competition",
                        "start": 633.12,
                    },
                    {
                        "text": "but additional hardware features that",
                        "start": 634.959,
                    },
                    {
                        "text": "get added to 3d",
                        "start": 637.04,
                    },
                    {
                        "text": "chips in the architecture end up costing",
                        "start": 638.88,
                    },
                    {
                        "text": "more money end up costing more r d money",
                        "start": 641.279,
                    },
                    {
                        "text": "and ultimately",
                        "start": 643.76,
                    },
                    {
                        "text": "would increase the cost of the system so",
                        "start": 645.279,
                    },
                    {
                        "text": "i think maybe they felt like these",
                        "start": 648.64,
                    },
                    {
                        "text": "features could have been left out in",
                        "start": 650.88,
                    },
                    {
                        "text": "order to keep the cost to where it was",
                        "start": 652.959,
                    },
                    {
                        "text": "at 299 us dollars but of course i am",
                        "start": 654.88,
                    },
                    {
                        "text": "speculating i really don't know why",
                        "start": 657.92,
                    },
                    {
                        "text": "those things were left out and if",
                        "start": 660.24,
                    },
                    {
                        "text": "someone that is more affiliated with",
                        "start": 661.68,
                    },
                    {
                        "text": "sony at the time has a better",
                        "start": 664.399,
                    },
                    {
                        "text": "understanding of why i would love to",
                        "start": 666.48,
                    },
                    {
                        "text": "hear the reasoning for you know some of",
                        "start": 668.64,
                    },
                    {
                        "text": "the omissions that were made but of",
                        "start": 670.88,
                    },
                    {
                        "text": "course it was also you know early 3d and",
                        "start": 672.48,
                    },
                    {
                        "text": "we were still kind of feeling our way",
                        "start": 675.519,
                    },
                    {
                        "text": "with the earliest 3d effects cards that",
                        "start": 680.32,
                    },
                    {
                        "text": "came out there were emissions in those",
                        "start": 682.8,
                    },
                    {
                        "text": "cards as well that you know had similar",
                        "start": 685.279,
                    },
                    {
                        "text": "types of issues but it did have a z",
                        "start": 687.92,
                    },
                    {
                        "text": "buffer i know that for a fact it",
                        "start": 690.88,
                    },
                    {
                        "text": "definitely had a z buffer but there was",
                        "start": 692.56,
                    },
                    {
                        "text": "you know the the texture warping stuff",
                        "start": 694.64,
                    },
                    {
                        "text": "that was going on in in some instances",
                        "start": 696.8,
                    },
                    {
                        "text": "as well that i certainly recall so who",
                        "start": 699.04,
                    },
                    {
                        "text": "knows maybe it was just you know the",
                        "start": 701.44,
                    },
                    {
                        "text": "you know the immaturity i guess or the",
                        "start": 704.399,
                    },
                    {
                        "text": "early days of 3d acceleration that was",
                        "start": 706.16,
                    },
                    {
                        "text": "something that you know hardware",
                        "start": 709.76,
                    },
                    {
                        "text": "manufacturers and architects were trying",
                        "start": 711.44,
                    },
                    {
                        "text": "to figure out as they were learning",
                        "start": 714.0,
                    },
                    {
                        "text": "about 3d and all the different ways to",
                        "start": 716.32,
                    },
                    {
                        "text": "get good 3d on you know a game console",
                        "start": 718.639,
                    },
                    {
                        "text": "or a pc well guys we're going to leave",
                        "start": 721.68,
                    },
                    {
                        "text": "it here for this video thank you so much",
                        "start": 724.24,
                    },
                    {
                        "text": "for watching if you liked it you know",
                        "start": 725.68,
                    },
                    {
                        "text": "what to do leave me a thumbs up and as",
                        "start": 727.12,
                    },
                    {
                        "text": "always don't forget to like and",
                        "start": 728.88,
                    },
                    {
                        "text": "subscribe and i'll catch you guys in the",
                        "start": 730.16,
                    },
                    {
                        "text": "next video bye for now",
                        "start": 732.16,
                    },
                    {
                        "text": "[Music]",
                        "start": 738.57,
                    },
                    {
                        "text": "[Music]",
                        "start": 745.25,
                    },
                    {
                        "text": "you",
                        "start": 755.2,
                    },
                ],
            },
        }
    }
