class BackendInputStream extends InputStream {
    private StringReader currentReader;
    static Boolean waitUserInput = true;

    @Override
    public int read() throws IOException {
        if (waitUserInput) {
            readFromInputServer();
            waitUserInput = false;
        }
        int character = currentReader.read();
        if (character == -1) waitUserInput = true;
        return character;
    }

    private void readFromInputServer() throws IOException {
        String scriptPath = "/tmp/lablup_input_stream.py";
        File f = new File(scriptPath);
        if (!f.exists()) {
            String s = "import socket\n\n"
                     + "with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:\n"
                     + "  try:\n"
                     + "    sk.connect('/tmp/bai-user-input.sock')\n"
                     + "    userdata = sk.recv(1024)\n"
                     + "  except ConnectRefusedError:\n"
                     + "    userdata = b'<user-input-unavailable>'\n"
                     + "print(userdata.decode())";
            try (PrintStream out = new PrintStream(
                    new FileOutputStream(scriptPath))) {
                out.print(s);
            }
        }
        String command = "python " + scriptPath;
        String output = executeCommand(command);
        currentReader = new StringReader(output);
    }

    private String executeCommand(String command) {
        StringBuffer output = new StringBuffer();
        Process p;
        try {
            p = Runtime.getRuntime().exec(command);
            p.waitFor();
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(p.getInputStream()));
            String line = "";
            while ((line = reader.readLine())!= null) {
                output.append(line + "\n");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return output.toString();
    }
}
