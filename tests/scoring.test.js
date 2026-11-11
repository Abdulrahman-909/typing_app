import test from 'node:test';import assert from 'node:assert/strict';import{score,units}from'../static/js/scoring.js';
test('known WPM',()=>assert.equal(score('hello world','hello world',60).wpm,2.2));
test('NFC equivalence',()=>assert.deepEqual(units('a\u0301'),units('á')));
test('whole word credit',()=>assert.equal(score('hello world','hello worlx',60).wpm,1.2));
test('corrected errors',()=>assert.equal(Math.round(score('hi','hi',1,3,1).accuracy),67));
test('zero elapsed',()=>assert.equal(score('a','a',0).wpm,0));
