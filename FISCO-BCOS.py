import click
import os
import re

init_yaml = """version: "3"

services:"""

node_yaml = """
  node{node_id}:
    image: fiscoorg/fiscobcos:latest
    ports:
      - "{channel_port}:{channel_port}"
      - "{rpc_port}:{rpc_port}"
      - "{p2p_port}:{p2p_port}"
    working_dir: /data
    volumes:
      - ./nodes/172.17.0.1/node{node_id}:/data
    deploy:
      resources:
        limits:
          cpus: "{limit_cpus}"
          memory: {limit_mem}M
        reservations:
          memory: {res_mem}M
    container_name: node{node_id}
    command: /data/start.sh
"""

depend_yaml = """    depends_on:
      - "node{prevNodeId}"
"""

@click.command()
@click.option('-c', '--count', default=1, help='Number of FISCO BCOS Chain.')
@click.option('-channel', '--channel-port', default=20200, help='ChannelPort of the first node.')
@click.option('-rpc', '--rpc-port', default=8545, help='RpcPort of the first node.')
@click.option('-p2p', '--p2p-port', default=30300, help='P2pPort of the first node.')
@click.option('-lcpus', '--limit-cpus', default=0.5, help='Limit cpus of node.')
@click.option('-lmem', '--limit-mem', default=300, help='Limit memory of node.')
@click.option('-rmem', '--res-mem', default=200, help='Reservations memory of node.')
def init_start(count, channel_port, rpc_port, p2p_port, limit_cpus, limit_mem, res_mem):
    os.system("chmod u+x build_chain.sh")
    os.system("bash build_chain.sh -l 172.17.0.1:{count} -p {p2p_port},{channel_port},{rpc_port}".format(count=count,
        p2p_port=p2p_port, channel_port=channel_port, rpc_port=rpc_port))

    docker_compose_yaml = ""
    docker_compose_filename = "docker-compose.yaml"
    for node_id in range(count):
        node_msg = node_yaml.format(node_id=node_id, channel_port=channel_port+node_id, rpc_port=rpc_port+node_id, 
            p2p_port=p2p_port+node_id, limit_cpus=limit_cpus, limit_mem=limit_mem, res_mem=res_mem)
    if node_id == 0:
        docker_compose_yaml += init_yaml
        docker_compose_yaml += node_msg
    else:
        docker_compose_yaml += node_msg
        docker_compose_yaml += depend_yaml.format(prevNodeId=node_id-1)

    with open(docker_compose_filename, 'w') as f:
        f.write(docker_compose_yaml)
    os.system("docker-compose --compatibility -f docker-compose.yaml up")

@click.command()
def add_node():
    maxNodeId = max([int(fn[4:]) for fn in os.listdir("./nodes/172.17.0.1") if "node" in fn])
    os.system("bash gen_node_cert.sh -c ./nodes/cert/agency -o node{node_id}".format(node_id=maxNodeId+1))
    os.system("mv node{node_id} ./nodes/172.17.0.1/node{node_id}".format(node_id=maxNodeId+1))
    os.system("cp ./nodes/172.17.0.1/node0/config.ini ./nodes/172.17.0.1/node{node_id}/".format(node_id=maxNodeId+1))
    with open("./nodes/172.17.0.1/node0/config.ini", "r") as r:
        node_txt = r.read()
    params = re.compile(r'listen_port=(\d+)')
    portList = re.findall(params, node_txt) # [channel_port, rpc_port, p2p_port]
    [first_channel_port, first_rpc_port, first_p2p_port] = [int(port) for port in portList]
    [new_channel_port, new_rpc_port, new_p2p_port] = [int(port)+maxNodeId+1 for port in portList]
    node_txt = node_txt.replace("="+str(first_channel_port), "="+str(new_channel_port))
    node_txt = node_txt.replace("="+str(first_rpc_port), "="+str(new_rpc_port))
    node_txt = node_txt.replace("="+str(first_p2p_port), "="+str(new_p2p_port))
    node_txt = node_txt.replace(
        "node.{node_id}=172.17.0.1:{rpc_port}"
            .format(node_id=maxNodeId, rpc_port=first_p2p_port+maxNodeId),
        "node.{node_id}=172.17.0.1:{rpc_port}"
            .format(node_id=maxNodeId, rpc_port=first_p2p_port+maxNodeId) + 
        "\n    node.{node_id}=172.17.0.1:{rpc_port}"
            .format(node_id=maxNodeId+1, rpc_port=first_p2p_port+maxNodeId+1),)
    with open("./nodes/172.17.0.1/node{node_id}/config.ini".format(node_id=maxNodeId+1), "w") as f:
        f.write(node_txt)
    # TODO: add new node to group

@click.command()
def start_fisco():
    os.system("docker-compose --compatibility -f docker-compose.yaml up")

@click.command()
def down_fisco():
    os.system("docker-compose -f docker-compose.yaml down")
    os.system("rm -rf ./nodes")

@click.group()
def cli():
    pass

cli.add_command(init_start)
cli.add_command(down_fisco)
cli.add_command(add_node)

if __name__ == '__main__':
    cli()