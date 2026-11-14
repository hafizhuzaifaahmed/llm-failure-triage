package org.apache.commons.lang3.math;

// PIPELINE-VALIDATION FIXTURE — hand-written by the implementation assistant, NOT a generated test and
// NOT research data. Each method is designed to exercise one ground-truth rule on Defects4J Lang-1
// (NumberUtils.createNumber("0x80000000") throws NumberFormatException on 1b and returns a Long on 1f).

import static org.junit.Assert.*;

import java.io.File;
import java.nio.file.Files;

import org.junit.Test;

public class HarnessFixtureTest {

    private static int bump(String name) throws Exception {
        File f = new File(System.getProperty("java.io.tmpdir"), "triage-fixture-" + name);
        int n = f.exists() ? Integer.parseInt(new String(Files.readAllBytes(f.toPath())).trim()) : 0;
        Files.write(f.toPath(), String.valueOf(n + 1).getBytes());
        return n;
    }

    @Test // expected PF: fails on B (NumberFormatException), passes on F
    public void expectPF() {
        assertEquals(Long.valueOf(0x80000000L), NumberUtils.createNumber("0x80000000"));
    }

    @Test // expected TF: wrong expected value, identical assertion failure on B and F
    public void expectTF() {
        assertEquals(Integer.valueOf(5), NumberUtils.createNumber("4"));
    }

    @Test // expected PASS
    public void expectPass() {
        assertEquals(Integer.valueOf(4), NumberUtils.createNumber("4"));
    }

    @Test(expected = NumberFormatException.class) // expected MISGUIDED: asserts the buggy behaviour
    public void expectMisguided() {
        NumberUtils.createNumber("0x80000000");
    }

    @Test // expected AMB: exception on B, assertion failure (different sigma) on F
    public void expectAmb() {
        Number n = NumberUtils.createNumber("0x80000000");
        assertNull(n);
    }

    @Test // expected TIMEOUT
    public void expectTimeout() {
        while (true) {
            Thread.yield();
        }
    }

    @Test // expected FLAKY: alternates fail/pass across runs via a counter file
    public void expectFlaky() throws Exception {
        assertTrue(bump("flaky") % 2 == 1);
    }

    @Test // expected to be pruned as non-compiling on both versions
    public void expectNC() {
        NumberUtils.thisMethodDoesNotExist("1");
    }
}
