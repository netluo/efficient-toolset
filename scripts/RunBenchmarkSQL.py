# -*- coding: utf-8 -*-
# @Time    : 2023/4/4 13:04
# @Author  : chengxiang.luo
# @Email   : zibuyu886@sina.cn
# @File    : RunBenchmarkSQL.py
# @Software: PyCharm
import logging
import random
import re
import subprocess
import time
from logging import handlers


class RunBenchmarkSQL:
    def __init__(self):
        self.cpus = [4, 8, 16, 32]
        self.cpu = 0
        self.unit_name = ''
        self.host = "10.1.251.111"
        self.port = 2883
        self.user = "sysbench@dst#eeodst"
        self.database = "sysbench"
        self.password = ''
        self.memory = 0

        self.logfile = 'run_bench_sql.log'
        # logger 写在init里
        self.fmt = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(self.logfile)
        self.logger.setLevel(logging.INFO)
        self.logger_handler = handlers.TimedRotatingFileHandler(filename=self.logfile, when='D',
                                                                backupCount=30, encoding='utf-8', interval=1)
        self.logger_handler.setFormatter(self.fmt)
        # # 如果对日志文件名没有特殊要求的话，可以不用设置suffix和extMatch，如果需要，一定要让它们匹配上。
        self.logger_handler.suffix = '%Y%m%d'
        self.logger_handler.extMatch = re.compile(r"^\d{8}$")
        self.logger.addHandler(self.logger_handler)

    def get_unit(self):
        units = ['u4c8g', 'u4c16g', 'u4c32g', 'u8c16g', 'u8c32g', 'u8c64g', 'u16c32g', 'u16c64g', 'u16c128g', 'u32c64g',
                 'u32c128g']
        for cpu in self.cpus:
            self.cpu = cpu
            for i in range(3):
                self.memory = cpu * (2 ** (i + 1))
                if self.memory == 256:
                    exit(0)
                print(cpu, self.memory)
                self.unit_name = 'u' + str(cpu) + 'c' + str(self.memory) + 'g'
                self.set_pool_unit()

    def set_pool_unit(self):
        _output_04 = subprocess.getoutput("obclient -h 10.1.251.111 -u root@sys#eeodst -P 2883 -c -A -p'AAbb11@#' "
                                          "-Doceanbase -e'alter system major freeze'")
        time.sleep(90)
        _output_01 = subprocess.getoutput(
            f"obclient -h 10.1.251.111 -u root@sys#eeodst -P 2883 -c -A -p'AAbb11@#' -Doceanbase -e'alter resource "
            f"pool pool_dst_zone1_jgt unit = {self.unit_name}'")
        _output_02 = subprocess.getoutput(
            f"obclient -h 10.1.251.111 -u root@sys#eeodst -P 2883 -c -A -p'AAbb11@#' -Doceanbase -e'alter resource "
            f"pool pool_dst_zone3_cjr unit = {self.unit_name}'")
        _output_03 = subprocess.getoutput(
            f"obclient -h 10.1.251.111 -u root@sys#eeodst -P 2883 -c -A -p'AAbb11@#' -Doceanbase -e'alter resource "
            f"pool pool_dst_zone2_kyq unit = {self.unit_name}'")
        self.logger.info("set pool unit.")
        self.get_stat(_output_01, _output_02, _output_03)

    def get_stat(self, _output_01, _output_02, _output_03):
        if _output_01 != '' or _output_02 != '' or _output_03 != '':
            self.logger.error('_output_01:' + _output_01 + ',_output_02:' + _output_02 + ',_output_03:' + _output_03)
            self.logger.info("alter system major freeze.")
            _output_04 = subprocess.getoutput("obclient -h 10.1.251.111 -u root@sys#eeodst -P 2883 -c -A -p'AAbb11@#' "
                                              "-Doceanbase -e'alter system major freeze'")
            time.sleep(90)
            self.set_pool_unit()
        else:
            self.logger.info('gen config(props).')
            self.gen_config()

    def gen_config(self):
        for i in range(10):
            warehouses = 10
            # 用户线程数，代表连接的用户数
            thd = random.randint(self.cpu, 5 * warehouses)

            # 测试时长，预计测试5-10m ,随机测试时长
            m = 3

            # ctime = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

            # newOrderWeight的数
            newOrderWeight = random.randint(40, 45)

            # paymentWeight的量
            paymentWeight = random.randint(newOrderWeight - 5, newOrderWeight)

            # 在BenchmarkSQL中，orderStatusWeight是一个表示订单状态权重的常量，用于在负载测试期间模拟具有不同状态的订单。根据BenchmarkSQL的文档，orderStatusWeight可以取以下值之一：
            #
            # 1：表示新订单（New
            # Order）状态，这是订单的默认状态。
            # 2：表示已确认订单（Confirmed
            # Order）状态。
            # 3：表示派送中订单（Delivery
            # Order）状态。
            # 4：表示已完成订单（Completed
            # Order）状态。
            # 5：表示已撤销订单（Canceled
            # Order）状态。
            # 这些状态对应于TPC - C基准测试规范中定义的订单状态。在BenchmarkSQL中，orderStatusWeight用于计算特定订单状态的数量，以便生成符合预期分布的订单状态。例如，如果将orderStatusWeight设置为2，则大约有20 % 的订单将具有“已确认”状态，而其他80 % 的订单将具有“新订单”状态。这样可以更好地模拟真实环境下的订单状态分布，从而评估系统的性能和可扩展性。
            orderStatusWeight = random.randint(1, 5)

            # stockLevelWeight 与 deliveryWeight 的值设置为基本一致状态
            stockLevelWeight = (
                    random.randint(1, 100 - newOrderWeight - paymentWeight - orderStatusWeight) / 2).__int__()
            deliveryWeight = 100 - newOrderWeight - paymentWeight - orderStatusWeight - stockLevelWeight

            # print(newOrderWeight + paymentWeight + deliveryWeight + stockLevelWeight)
            prop_file_name = f'{self.unit_name}_{thd}_{newOrderWeight}_{paymentWeight}_{orderStatusWeight}_{deliveryWeight}_{stockLevelWeight}'
            temple_file = f"""
db=oceanbase
driver=com.alipay.oceanbase.jdbc.Driver
conn=jdbc:oceanbase://10.1.44.137:2883/sysbench?useUnicode=true&characterEncoding=utf-8&rewriteBatchedStatements=true&allowMultiQueries=true
user=sysbench@dst#eeodst
password=
//Unit Config : {self.unit_name}
warehouses={warehouses}
loadWorkers={warehouses + 1}
//fileLocation=/data/temp/

terminals={thd}
//To run specified transactions per terminal- runMins must equal zero
runTxnsPerTerminal=0
//To run for specified minutes- runTxnsPerTerminal must equal zero
runMins={m}
//Number of total transactions per minute
limitTxnsPerMin=0

//Set to true to run in 4.x compatible mode. Set to false to use the
//entire configured database evenly.
terminalWarehouseFixed=true

//The following five values must add up to 100
newOrderWeight={newOrderWeight}
paymentWeight={paymentWeight}
orderStatusWeight={orderStatusWeight}
deliveryWeight={deliveryWeight}
stockLevelWeight={stockLevelWeight}

// Directory name to create for collecting detailed result data.
// Comment this out to suppress.
resultDirectory=obprops_res/{self.unit_name}_{thd}_{newOrderWeight}_{paymentWeight}_{orderStatusWeight}_{deliveryWeight}_{stockLevelWeight}
osCollectorScript=./misc/os_collector_linux.py
osCollectorInterval=1
//osCollectorSSHAddr=user@dbhost
//osCollectorDevices=net_eth0 blk_sda
    """

            with open(
                    f'/data1/benchmarksql-5.0/run/obprops/prop.{prop_file_name}',
                    'w+',
                    encoding='utf8') as f:
                f.writelines(
                    temple_file.format(threads=thd, mins_to_run=m, newOrderWeight=newOrderWeight,
                                       paymentWeight=paymentWeight,
                                       deliveryWeight=deliveryWeight, stockLevelWeight=stockLevelWeight))
                f.close()
                self.logger.info(f"gen prop: prop.{prop_file_name}")
            state_code = self.run_bench_mark(prop_file_name)
            time.sleep(200)
            if state_code == 0:
                self.logger.info("state_code:" + state_code.__str__())

    def run_bench_mark(self, prop_file_name):
        self.logger.info(f"run benchmark: prop.{prop_file_name}")
        output = subprocess.getstatusoutput(
            f"./runBenchmark.sh obprops/prop.{prop_file_name} >> {self.unit_name}_run_bench_sql.log")
        self.logger.info(output[1])
        return output[0]


if __name__ == '__main__':
    rbs = RunBenchmarkSQL()
    rbs.get_unit()
