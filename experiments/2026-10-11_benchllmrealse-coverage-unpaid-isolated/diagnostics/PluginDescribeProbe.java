import java.io.File;
import org.eclipse.jgit.api.Git;
import pl.project13.jgit.DescribeCommand;
import pl.project13.maven.git.log.StdOutLoggerBridge;

/** Exercises the actual git-commit-id-plugin 2.1.13 describe implementation. */
public final class PluginDescribeProbe {
    public static void main(String[] args) throws Exception {
        Git git = Git.open(new File(args[0]));
        try {
            System.out.println(DescribeCommand.on(git.getRepository())
                .withLoggerBridge(new StdOutLoggerBridge(false)).tags(true).call());
        } finally {
            git.close();
        }
    }
}
