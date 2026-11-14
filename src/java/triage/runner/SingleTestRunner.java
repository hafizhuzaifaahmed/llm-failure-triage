package triage.runner;

import java.io.PrintWriter;
import java.io.StringWriter;

import org.junit.runner.JUnitCore;
import org.junit.runner.Request;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;

/**
 * Runs exactly one JUnit 4 test method and prints one result record between markers.
 * Invoked once per run in a fresh JVM by triage/execution.py (Phase 2, C6).
 *
 * Output fields (tab-free, one per line, values escaped):
 *   outcome   pass | assertion_failure | exception | harness_error
 *   exception fully qualified exception class (empty on pass)
 *   message   exception message
 *   trace     full stack trace
 */
public final class SingleTestRunner {

    private static String esc(String s) {
        if (s == null) return "";
        return s.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r");
    }

    private static boolean isAssertion(Throwable t) {
        // JUnit 4 assertions, JUnit 3 AssertionFailedError and hamcrest all surface as AssertionError
        // or junit.framework.AssertionFailedError.
        return t instanceof AssertionError
                || t.getClass().getName().equals("junit.framework.AssertionFailedError")
                || t.getClass().getName().equals("junit.framework.ComparisonFailure");
    }

    public static void main(String[] args) {
        String outcome, exClass = "", message = "", trace = "";
        try {
            Class<?> cls = Class.forName(args[0], true, SingleTestRunner.class.getClassLoader());
            Result r = new JUnitCore().run(Request.method(cls, args[1]));
            if (r.getRunCount() == 0 && r.getFailureCount() == 0) {
                outcome = "harness_error";
                message = "no test was run (method not found or ignored)";
            } else if (r.wasSuccessful()) {
                outcome = "pass";
            } else {
                Failure f = r.getFailures().get(0);
                Throwable t = f.getException();
                // getDisplayName() exists since JUnit 4.0; getMethodName() (4.6+) threw NoSuchMethodError when a project
                // ships an older JUnit ahead of ours on the classpath (D-43). Display name = "method(class)".
                String desc = f.getDescription() == null ? "" : String.valueOf(f.getDescription().getDisplayName());
                if (t == null) {
                    outcome = "harness_error";
                } else if (desc.startsWith("initializationError")
                        || t instanceof NoClassDefFoundError || t instanceof ClassNotFoundException
                        || (t instanceof Exception && String.valueOf(t.getMessage()).startsWith("No tests found"))) {
                    outcome = "harness_error";
                } else if (t instanceof OutOfMemoryError) {
                    outcome = "harness_error";
                } else {
                    outcome = isAssertion(t) ? "assertion_failure" : "exception";
                }
                if (t != null) {
                    exClass = t.getClass().getName();
                    message = String.valueOf(t.getMessage());
                    StringWriter sw = new StringWriter();
                    t.printStackTrace(new PrintWriter(sw));
                    trace = sw.toString();
                }
            }
        } catch (Throwable t) {
            outcome = "harness_error";
            exClass = t.getClass().getName();
            message = String.valueOf(t.getMessage());
        }
        System.out.println("<<<TRIAGE-RESULT>>>");
        System.out.println("outcome=" + outcome);
        System.out.println("exception=" + esc(exClass));
        System.out.println("message=" + esc(message));
        System.out.println("trace=" + esc(trace));
        System.out.println("<<<END-TRIAGE-RESULT>>>");
        System.out.flush();
        // A generated test may leave non-daemon threads behind; never let them hold the JVM open.
        System.exit(0);
    }
}
