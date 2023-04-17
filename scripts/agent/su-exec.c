/* forked from https://github.com/ncopa/su-exec */
/* set user and group id and exec */

#include <sys/types.h>

#include <err.h>
#include <errno.h>
#include <grp.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static char *argv0;

static void usage(int exitcode)
{
        printf("Usage: %s user-spec command [args]\n", argv0);
        exit(exitcode);
}

int str_occurrences(char *str, char tok)
{
        int i, count = 0;
        for (i = 0; str[i]; i++)
        {
                if (str[i] == tok)
                        count += 1;
        }
        return count;
}

gid_t get_gid(char *ref)
{
        char *end;

        gid_t ngid = strtol(ref, &end, 10);
        if (*end == '\0')
                return ngid;
        else
        {
                struct group *gr = getgrnam(ref);
                if (gr == NULL)
                        err(1, "getgrnam(%s)", ref);
                return gr->gr_gid;
        }
}

int main(int argc, char *argv[])
{
        char *user, *group, **cmdargv;
        char *end;

        uid_t uid = getuid();
        gid_t gid = getgid();

        argv0 = argv[0];
        if (argc < 3)
                usage(0);

        user = argv[1];
        group = strchr(user, ':');
        if (group)
                *group++ = '\0';

        cmdargv = &argv[2];

        struct passwd *pw = NULL;
        if (user[0] != '\0')
        {
                uid_t nuid = strtol(user, &end, 10);
                if (*end == '\0')
                        uid = nuid;
                else
                {
                        pw = getpwnam(user);
                        if (pw == NULL)
                                err(1, "getpwnam(%s)", user);
                }
        }
        if (pw == NULL)
        {
                pw = getpwuid(uid);
        }
        if (pw != NULL)
        {
                uid = pw->pw_uid;
                gid = pw->pw_gid;
        }

        setenv("HOME", pw != NULL ? pw->pw_dir : "/", 1);

        if (group && group[0] != '\0')
        {
                /* group was specified, ignore grouplist for setgroups later */
                pw = NULL;
                int group_cnt;

                group_cnt = str_occurrences(group, ',') + 1;
                if (group_cnt == 1)
                {
                        gid = get_gid(group);
                        if (setgroups(1, &gid) < 0)
                                err(1, "setgroups(%i)", gid);
                }
                else
                {
                        char *token;
                        gid_t *gidlist;
                        int i = 0;

                        gidlist = (gid_t *)malloc(sizeof(gid_t) * (group_cnt));

                        token = strtok(group, ",");
                        gid = get_gid(token);
                        *gidlist = gid;

                        token = strtok(NULL, ",");
                        while (token != NULL)
                        {
                                i += 1;
                                *(gidlist + i) = get_gid(token);
                                token = strtok(NULL, ",");
                        }
                        if (setgroups(group_cnt, gidlist) < 0)
                                err(1, "setgroups()");
                }
        }

        if (pw != NULL)
        {
                int ngroups = 0;
                gid_t *glist = NULL;

                while (1)
                {
                        int r = getgrouplist(pw->pw_name, gid, glist, &ngroups);

                        if (r >= 0)
                        {
                                if (setgroups(ngroups, glist) < 0)
                                        err(1, "setgroups");
                                break;
                        }

                        glist = realloc(glist, ngroups * sizeof(gid_t));
                        if (glist == NULL)
                                err(1, "malloc");
                }
        }

        if (setgid(gid) < 0)
                err(1, "setgid(%i)", gid);

        if (setuid(uid) < 0)
                err(1, "setuid(%i)", uid);

        execvp(cmdargv[0], cmdargv);
        err(1, "%s", cmdargv[0]);

        return 1;
}