var WebSocketClient = require("websocket").client;
const axios = require("axios");

const connect = async () => {
    var client = new WebSocketClient();

    const auth = await axios.default.get(
        'https://test.deribit.com/api/v2/public/auth',
        {
            params: {
                client_id: 'HD5Poh0t',
                client_secret: "B4rgiZopaPg83Od0oah037IUPJ96teR8-1svxUmeFB8",
                grant_type: "client_credentials",
            },
        }
    );
    const access_token = auth.data.result.access_token;
    return new Promise((resolve, reject) => {
        client.on("connect", async function (connection) {
            console.log("WebSocket Client Connected");
            const msg = {
                jsonrpc: "2.0",
                method: "private/subscribe",
                params: {
                    channels: [`ticker.BTC-29DEC23-16000-C.raw`, `ticker.BTC-29DEC23-18000-C.raw`, `ticker.BTC-29DEC23-20000-C.raw`],
                    access_token
                },
            }
            if (connection.connected) {
                connection.sendUTF(JSON.stringify(msg));
            }
            connection.on("error", function (error) {
                console.log("Connection Error: " + error.toString());
            });
            connection.on("closed", function (error) {
                console.log("Connection closed: ");
            });
            connection.on("message", function (message) {
                const response = JSON.parse(message.utf8Data);
                if (response.method == "subscription") {
                    const params = response.params;
                    const channel = `${params.channel}`.split(".");
                    if (channel[0] === "ticker") {
                        const data = params.data;
                        // TODO: data to be persisted
                        console.log(data);
                    }
                }
            });
        });
        client.connect("wss://test.deribit.com/ws/api/v2");
    });
};

connect()