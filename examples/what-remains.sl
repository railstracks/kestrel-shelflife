// what remains
// six memories, three attention slots, one choice
//
// This program is designed to fail beautifully.
// Values decay naturally. Only one is remembered.
// The ? marks are not errors — they are the output.

let sky = "the color of the sky that day"
print sky

let hand = "the weight of your hand"
print hand
// sky is fading

let words = "the last thing you said"
remember words
print words

let door = "the sound of the door"
print door
// hand is fading

let quiet = "the silence after"
print quiet
// door is fading

let nothing = "nothing"
print nothing

// time passes
let _ = 0
let _ = 0

// what do I still know?
print sky
print hand
print words
print door
print quiet
print nothing

// only one thing remains
print words
