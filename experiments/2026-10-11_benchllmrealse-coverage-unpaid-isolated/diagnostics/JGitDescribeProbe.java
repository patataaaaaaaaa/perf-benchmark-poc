import java.io.File;
import org.eclipse.jgit.api.Git;

/** Runs only in local, synthetic shallow repositories, never an experiment checkout. */
public final class JGitDescribeProbe {
    public static void main(String[] args) throws Exception {
        Git git = Git.open(new File(args[0]));
        try {
            System.out.println(git.describe().call());
        } finally {
            git.close();
        }
    }
}
