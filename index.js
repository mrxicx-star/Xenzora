const { Client, GatewayIntentBits, EmbedBuilder } = require("discord.js");

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

const prefix = ",";

client.once("ready", () => {
  console.log("Xrenza is online!");
});

client.on("messageCreate", async (message) => {
  if (!message.content.startsWith(prefix) || message.author.bot) return;

  const args = message.content.slice(prefix.length).trim().split(/ +/);
  const command = args.shift().toLowerCase();

  if (command === "help") {
    const embed = new EmbedBuilder()
      .setColor("Purple")
      .setTitle("🔥 Xrenza Help Menu")
      .setDescription("Available Commands")
      .addFields(
        { name: "General", value: "`help`, `ping`, `avatar`" },
        { name: "Moderation", value: "`ban`, `kick`, `mute`" }
      );

    return message.reply({ embeds: [embed] });
  }

  if (command === "ping") return message.reply("🏓 Pong!");
  if (command === "avatar") return message.reply(message.author.displayAvatarURL());

  if (command === "ban") return message.reply("🔨 Ban command example.");
  if (command === "kick") return message.reply("👢 Kick command example.");
  if (command === "mute") return message.reply("🔇 Mute command example.");
});

client.login(process.env.TOKEN);
