// JavaScript function to generate 6 random unique values in order and populate form
function luckyDip() {

    // create empty set
    let draw = new Set();

    // generate cryptographically secure random numbers to use
    let randomBuffer = new Uint32Array(1000);
    window.crypto.getRandomValues(randomBuffer);

    let i = 0;
    // while set does not contain 6 values, create a random value between 1 and 60
    while (draw.size < 6) {
        i++;
        min = Math.ceil(1);
        max = Math.floor(60);
        value = Math.floor((randomBuffer[i] * (max - min + 1) + min) / 4294967295);
        // sets cannot contain duplicates so value is only added if it does not exist in set
        draw.add(value);
    }

    // turn set into an array
    let a = Array.from(draw);

    // sort array into size order
    a.sort(function (a, b) {
        return a - b;
    });

    // add values to fields in create draw form
    for (let i = 0; i < 6; i++) {
        document.getElementById("no" + (i + 1)).value = a[i];
    }
}